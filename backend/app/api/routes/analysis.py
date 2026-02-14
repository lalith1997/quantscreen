"""
Analysis API routes.
Serves strategy recommendations for individual stocks.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import StockStrategy

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/{ticker}/strategy")
async def get_stock_strategy(ticker: str, db: Session = Depends(get_db)):
    """
    Get strategy recommendations for a stock across all timeframes.
    Returns the most recent analysis for swing, position, and long-term.
    """
    ticker = ticker.upper()

    strategies = (
        db.query(StockStrategy)
        .filter(StockStrategy.ticker == ticker)
        .order_by(StockStrategy.analysis_date.desc())
        .limit(10)
        .all()
    )

    if not strategies:
        raise HTTPException(
            status_code=404,
            detail=f"No strategies found for {ticker}. Run daily analysis first.",
        )

    # Get the latest analysis date
    latest_date = strategies[0].analysis_date

    # Group by timeframe for the latest date
    result = {}
    for s in strategies:
        if s.analysis_date != latest_date:
            break
        result[s.timeframe] = {
            "timeframe": s.timeframe,
            "entry_price": float(s.entry_price) if s.entry_price else None,
            "stop_loss": float(s.stop_loss) if s.stop_loss else None,
            "take_profit": float(s.take_profit) if s.take_profit else None,
            "risk_reward_ratio": (
                float(s.risk_reward_ratio) if s.risk_reward_ratio else None
            ),
            "confidence": s.confidence,
            "rationale": s.rationale,
            "signals": s.signals or {},
            "analysis_date": s.analysis_date.isoformat(),
        }

    return {
        "ticker": ticker,
        "analysis_date": latest_date.isoformat(),
        "strategies": result,
    }
