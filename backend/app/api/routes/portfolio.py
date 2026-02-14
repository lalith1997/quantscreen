"""
Portfolio API routes.
Manage holdings, run health checks, and view alerts.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.core.database import get_db
from app.models import PortfolioHolding, PortfolioSnapshot, PortfolioAlert
from app.schemas import (
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/")
async def get_holdings(db: Session = Depends(get_db)):
    """Get all active holdings with live prices and P&L."""
    from app.services.portfolio_service import get_holdings_with_prices

    holdings = await get_holdings_with_prices(db)
    return holdings


@router.post("/add")
async def add_holding(
    holding: PortfolioHoldingCreate,
    db: Session = Depends(get_db),
):
    """Add a single holding to the portfolio."""
    new_holding = PortfolioHolding(
        ticker=holding.ticker.upper(),
        shares=holding.shares,
        avg_cost_basis=holding.avg_cost_basis,
        buy_date=holding.buy_date,
        notes=holding.notes,
    )
    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)

    return {
        "id": new_holding.id,
        "ticker": new_holding.ticker,
        "shares": float(new_holding.shares),
        "avg_cost_basis": float(new_holding.avg_cost_basis),
        "buy_date": new_holding.buy_date.isoformat() if new_holding.buy_date else None,
        "notes": new_holding.notes,
        "message": f"Added {new_holding.ticker} to portfolio",
    }


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and import holdings from a CSV file."""
    from app.services.portfolio_service import parse_csv_holdings

    content = await file.read()
    csv_text = content.decode("utf-8")

    parsed = parse_csv_holdings(csv_text)

    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="No valid holdings found in CSV. Expected columns: ticker, shares, avg_cost_basis (or cost/price)",
        )

    added = []
    for entry in parsed:
        buy_date = None
        if "buy_date" in entry:
            try:
                buy_date = date.fromisoformat(entry["buy_date"])
            except (ValueError, TypeError):
                pass

        h = PortfolioHolding(
            ticker=entry["ticker"],
            shares=entry["shares"],
            avg_cost_basis=entry["avg_cost_basis"],
            buy_date=buy_date,
            notes=entry.get("notes"),
        )
        db.add(h)
        added.append(entry["ticker"])

    db.commit()

    return {
        "imported": len(added),
        "tickers": added,
        "message": f"Successfully imported {len(added)} holdings",
    }


@router.put("/{holding_id}")
async def update_holding(
    holding_id: int,
    update: PortfolioHoldingUpdate,
    db: Session = Depends(get_db),
):
    """Update a portfolio holding."""
    holding = db.query(PortfolioHolding).filter(PortfolioHolding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    if update.shares is not None:
        holding.shares = update.shares
    if update.avg_cost_basis is not None:
        holding.avg_cost_basis = update.avg_cost_basis
    if update.buy_date is not None:
        holding.buy_date = update.buy_date
    if update.notes is not None:
        holding.notes = update.notes

    db.commit()
    return {"message": f"Updated {holding.ticker}", "id": holding.id}


@router.delete("/{holding_id}")
async def delete_holding(
    holding_id: int,
    db: Session = Depends(get_db),
):
    """Soft-delete a holding (mark inactive)."""
    holding = db.query(PortfolioHolding).filter(PortfolioHolding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    holding.is_active = False
    db.commit()
    return {"message": f"Removed {holding.ticker} from portfolio", "id": holding.id}


@router.get("/analysis")
async def run_analysis(db: Session = Depends(get_db)):
    """Run an on-demand portfolio health check."""
    from app.services.portfolio_service import run_portfolio_analysis

    await run_portfolio_analysis(db)

    # Return latest snapshot
    snapshot = (
        db.query(PortfolioSnapshot)
        .order_by(PortfolioSnapshot.snapshot_date.desc())
        .first()
    )

    if not snapshot:
        return {"message": "Analysis completed but no snapshot created (no holdings?)"}

    return {
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "total_value": float(snapshot.total_value) if snapshot.total_value else None,
        "total_cost": float(snapshot.total_cost) if snapshot.total_cost else None,
        "total_gain_loss": float(snapshot.total_gain_loss) if snapshot.total_gain_loss else None,
        "total_gain_loss_pct": float(snapshot.total_gain_loss_pct) if snapshot.total_gain_loss_pct else None,
        "holdings_data": snapshot.holdings_data or {},
    }


@router.get("/alerts")
async def get_alerts(
    unread_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """Get portfolio alerts."""
    query = db.query(PortfolioAlert).order_by(PortfolioAlert.created_at.desc())
    if unread_only:
        query = query.filter(PortfolioAlert.is_read == False)

    alerts = query.limit(100).all()

    return [
        {
            "id": a.id,
            "ticker": a.ticker,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "is_read": a.is_read,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
):
    """Mark an alert as read."""
    alert = db.query(PortfolioAlert).filter(PortfolioAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    db.commit()
    return {"message": "Alert marked as read", "id": alert.id}


@router.get("/snapshots")
async def get_snapshots(
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    """Get historical portfolio snapshots."""
    cutoff = date.today() - timedelta(days=days)
    snapshots = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.snapshot_date >= cutoff)
        .order_by(PortfolioSnapshot.snapshot_date.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "snapshot_date": s.snapshot_date.isoformat(),
            "total_value": float(s.total_value) if s.total_value else None,
            "total_cost": float(s.total_cost) if s.total_cost else None,
            "total_gain_loss": float(s.total_gain_loss) if s.total_gain_loss else None,
            "total_gain_loss_pct": float(s.total_gain_loss_pct) if s.total_gain_loss_pct else None,
            "holdings_data": s.holdings_data or {},
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in snapshots
    ]
