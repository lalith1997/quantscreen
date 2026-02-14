"""
Market risk API routes.
Serves market risk assessment snapshots.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import MarketRiskSnapshot

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/risk-summary")
async def get_risk_summary(db: Session = Depends(get_db)):
    """Get the latest market risk assessment."""
    snapshot = (
        db.query(MarketRiskSnapshot)
        .order_by(MarketRiskSnapshot.snapshot_date.desc())
        .first()
    )

    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail="No market risk data available. Trigger analysis via POST /api/daily-brief/trigger",
        )

    return {
        "risk_score": snapshot.risk_score,
        "risk_label": snapshot.risk_label,
        "vix_level": float(snapshot.vix_level) if snapshot.vix_level else None,
        "sp500_price": float(snapshot.sp500_price) if snapshot.sp500_price else None,
        "sp500_change_pct": (
            float(snapshot.sp500_change_pct) if snapshot.sp500_change_pct else None
        ),
        "sector_data": snapshot.sector_data or {},
        "breadth_data": snapshot.breadth_data or {},
        "summary_text": snapshot.summary_text,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
    }
