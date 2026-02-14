"""
News API routes.
Serves stock-specific and market news with sentiment analysis.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import NewsArticle

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/market")
async def get_market_news(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get general market news."""
    articles = (
        db.query(NewsArticle)
        .filter(NewsArticle.ticker.is_(None))
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )

    return [_serialize_article(a) for a in articles]


@router.get("/{ticker}")
async def get_stock_news(
    ticker: str,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get news for a specific stock with impact assessment."""
    articles = (
        db.query(NewsArticle)
        .filter(NewsArticle.ticker == ticker.upper())
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )

    return [_serialize_article(a) for a in articles]


def _serialize_article(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "ticker": a.ticker,
        "title": a.title,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "sentiment": a.sentiment,
        "impact_score": float(a.impact_score) if a.impact_score else None,
        "impact_explanation": a.impact_explanation,
    }
