"""
Daily Brief API routes.
Serves pre-computed daily analysis results.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.core.database import get_db
from app.models import (
    DailyAnalysisRun,
    DailyPick,
    StockStrategy,
    NewsArticle,
    MarketRiskSnapshot,
)

router = APIRouter(prefix="/daily-brief", tags=["Daily Brief"])


@router.get("/")
async def get_latest_daily_brief(db: Session = Depends(get_db)):
    """
    Get the most recent completed daily analysis.
    Returns picks grouped by screen, market risk, strategies, and news.
    """
    run = (
        db.query(DailyAnalysisRun)
        .filter(DailyAnalysisRun.status == "completed")
        .order_by(DailyAnalysisRun.run_date.desc())
        .first()
    )

    if not run:
        raise HTTPException(
            status_code=404,
            detail="No daily analysis available yet. Trigger one via POST /api/daily-brief/trigger",
        )

    picks = db.query(DailyPick).filter(DailyPick.run_id == run.id).all()

    # Group picks by screen_name
    grouped = {}
    all_tickers = set()
    for pick in picks:
        all_tickers.add(pick.ticker)
        entry = {
            "ticker": pick.ticker,
            "rank": pick.rank,
            "metrics": pick.metrics,
            "rationale": pick.rationale,
            "earnings_date": pick.earnings_date.isoformat() if pick.earnings_date else None,
            "earnings_proximity": pick.earnings_proximity,
            "eps_estimated": float(pick.eps_estimated) if pick.eps_estimated else None,
        }
        grouped.setdefault(pick.screen_name, []).append(entry)

    # Fetch strategies for all picked stocks
    strategies = (
        db.query(StockStrategy)
        .filter(
            StockStrategy.ticker.in_(all_tickers),
            StockStrategy.analysis_date == run.run_date,
        )
        .all()
    )
    strategy_map = {}
    for s in strategies:
        strategy_map.setdefault(s.ticker, {})[s.timeframe] = {
            "timeframe": s.timeframe,
            "entry_price": float(s.entry_price) if s.entry_price else None,
            "stop_loss": float(s.stop_loss) if s.stop_loss else None,
            "take_profit": float(s.take_profit) if s.take_profit else None,
            "risk_reward_ratio": float(s.risk_reward_ratio) if s.risk_reward_ratio else None,
            "confidence": s.confidence,
            "rationale": s.rationale,
            "signals": s.signals or {},
            "analysis_date": s.analysis_date.isoformat(),
        }

    # Fetch recent news for picked stocks
    news_articles = (
        db.query(NewsArticle)
        .filter(NewsArticle.ticker.in_(all_tickers))
        .order_by(NewsArticle.published_at.desc())
        .limit(200)
        .all()
    )
    news_map = {}
    for a in news_articles:
        news_map.setdefault(a.ticker, []).append({
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "sentiment": a.sentiment,
            "impact_score": float(a.impact_score) if a.impact_score else None,
            "impact_explanation": a.impact_explanation,
        })

    # Attach strategies and news to picks
    for screen_name, pick_list in grouped.items():
        for pick in pick_list:
            ticker = pick["ticker"]
            pick["strategies"] = strategy_map.get(ticker, {})
            pick["news"] = news_map.get(ticker, [])[:5]  # Top 5 news per stock

    # Market risk
    risk = (
        db.query(MarketRiskSnapshot)
        .order_by(MarketRiskSnapshot.snapshot_date.desc())
        .first()
    )
    market_risk = None
    if risk:
        market_risk = {
            "risk_score": risk.risk_score,
            "risk_label": risk.risk_label,
            "vix_level": float(risk.vix_level) if risk.vix_level else None,
            "sp500_price": float(risk.sp500_price) if risk.sp500_price else None,
            "sp500_change_pct": float(risk.sp500_change_pct) if risk.sp500_change_pct else None,
            "sector_data": risk.sector_data or {},
            "breadth_data": risk.breadth_data or {},
            "summary_text": risk.summary_text,
            "snapshot_date": risk.snapshot_date.isoformat(),
        }

    return {
        "run_date": run.run_date.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "stocks_analyzed": run.stocks_analyzed,
        "stocks_passed": run.stocks_passed,
        "execution_time_seconds": (
            float(run.execution_time_seconds) if run.execution_time_seconds else None
        ),
        "picks_by_screen": grouped,
        "market_risk": market_risk,
    }


@router.get("/history")
async def get_daily_brief_history(
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    """Get past daily brief summaries."""
    cutoff = date.today() - timedelta(days=days)
    runs = (
        db.query(DailyAnalysisRun)
        .filter(
            DailyAnalysisRun.run_date >= cutoff,
            DailyAnalysisRun.status == "completed",
        )
        .order_by(DailyAnalysisRun.run_date.desc())
        .all()
    )

    return [
        {
            "run_date": r.run_date.isoformat(),
            "stocks_analyzed": r.stocks_analyzed,
            "stocks_passed": r.stocks_passed,
            "execution_time_seconds": (
                float(r.execution_time_seconds) if r.execution_time_seconds else None
            ),
        }
        for r in runs
    ]


@router.get("/picks")
async def get_todays_picks(
    screen: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get today's filtered picks, optionally by screen name."""
    run = (
        db.query(DailyAnalysisRun)
        .filter(DailyAnalysisRun.status == "completed")
        .order_by(DailyAnalysisRun.run_date.desc())
        .first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="No analysis available")

    query = db.query(DailyPick).filter(DailyPick.run_id == run.id)
    if screen:
        query = query.filter(DailyPick.screen_name == screen)

    picks = query.order_by(DailyPick.rank).all()

    return [
        {
            "ticker": p.ticker,
            "rank": p.rank,
            "screen_name": p.screen_name,
            "metrics": p.metrics,
            "rationale": p.rationale,
            "earnings_date": p.earnings_date.isoformat() if p.earnings_date else None,
            "earnings_proximity": p.earnings_proximity,
            "eps_estimated": float(p.eps_estimated) if p.eps_estimated else None,
        }
        for p in picks
    ]


@router.post("/trigger")
async def trigger_analysis(force: bool = False):
    """Manually trigger a daily analysis run. Use ?force=true to re-run even if already completed today."""
    from app.services.daily_engine import run_daily_analysis

    asyncio.create_task(run_daily_analysis(force=force))
    return {
        "status": "triggered",
        "message": "Daily analysis started in background. Check GET /api/daily-brief for results.",
    }
