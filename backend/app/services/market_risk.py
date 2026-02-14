"""
Market risk assessment service.
Computes a daily 1-10 risk score using VIX, S&P 500, sector performance, and breadth.
"""

from datetime import date
from sqlalchemy.orm import Session

from app.models import MarketRiskSnapshot
from app.services.data_providers import fmp_provider


async def compute_market_risk(db: Session) -> MarketRiskSnapshot | None:
    """Compute and store daily market risk assessment."""
    today = date.today()

    # Fetch market data from FMP
    indexes = await fmp_provider.get_market_indexes()
    sectors = await fmp_provider.get_sector_performance()
    gl = await fmp_provider.get_gainers_losers()

    # Extract VIX and S&P 500
    vix_level = None
    sp500_price = None
    sp500_change = None

    for idx in indexes:
        symbol = (idx.get("symbol") or "").upper()
        if "VIX" in symbol:
            vix_level = idx.get("price")
        if "GSPC" in symbol or symbol == "^GSPC":
            sp500_price = idx.get("price")
            sp500_change = idx.get("changesPercentage")

    # Sector performance data
    sector_data = {}
    for s in sectors:
        name = s.get("sector", "Unknown")
        change = s.get("changesPercentage")
        if change is not None:
            # FMP returns as string like "1.234%", strip the %
            if isinstance(change, str):
                change = change.replace("%", "")
                try:
                    change = float(change)
                except ValueError:
                    continue
            sector_data[name] = round(change, 2)

    # Breadth indicators
    gainers = gl.get("gainers", [])
    losers = gl.get("losers", [])
    gainers_count = len(gainers)
    losers_count = len(losers)
    advance_decline = (
        round(gainers_count / losers_count, 2) if losers_count > 0 else 1.0
    )

    breadth_data = {
        "advance_decline_ratio": advance_decline,
        "gainers_count": gainers_count,
        "losers_count": losers_count,
    }

    # Compute risk score (1 = very low risk, 10 = extreme risk)
    risk_score = _compute_risk_score(vix_level, sp500_change, advance_decline)
    risk_label = _risk_label(risk_score)
    summary = _build_summary(
        risk_score, risk_label, vix_level, sp500_price, sp500_change, sector_data
    )

    # Upsert snapshot
    existing = (
        db.query(MarketRiskSnapshot)
        .filter(MarketRiskSnapshot.snapshot_date == today)
        .first()
    )

    if existing:
        existing.risk_score = risk_score
        existing.risk_label = risk_label
        existing.vix_level = vix_level
        existing.sp500_price = sp500_price
        existing.sp500_change_pct = sp500_change
        existing.sector_data = sector_data
        existing.breadth_data = breadth_data
        existing.summary_text = summary
        snapshot = existing
    else:
        snapshot = MarketRiskSnapshot(
            snapshot_date=today,
            risk_score=risk_score,
            risk_label=risk_label,
            vix_level=vix_level,
            sp500_price=sp500_price,
            sp500_change_pct=sp500_change,
            sector_data=sector_data,
            breadth_data=breadth_data,
            summary_text=summary,
        )
        db.add(snapshot)

    db.commit()
    return snapshot


def _compute_risk_score(
    vix: float | None,
    sp500_change: float | None,
    ad_ratio: float | None,
) -> int:
    """
    Compute market risk on a 1-10 scale.

    Factors:
    - VIX level: Fear gauge. >35 = panic, <12 = complacency
    - S&P 500 daily change: Large drops increase risk
    - Advance/decline ratio: Market breadth health
    """
    score = 5  # Neutral baseline

    # VIX impact
    if vix is not None:
        if vix > 35:
            score += 3
        elif vix > 25:
            score += 2
        elif vix > 20:
            score += 1
        elif vix < 12:
            score -= 2
        elif vix < 15:
            score -= 1

    # S&P 500 daily move
    if sp500_change is not None:
        if sp500_change < -3:
            score += 3
        elif sp500_change < -2:
            score += 2
        elif sp500_change < -1:
            score += 1
        elif sp500_change > 2:
            score -= 1
        elif sp500_change > 1:
            score -= 1

    # Breadth
    if ad_ratio is not None:
        if ad_ratio < 0.5:
            score += 1
        elif ad_ratio > 2.0:
            score -= 1

    return max(1, min(10, score))


def _risk_label(score: int) -> str:
    """Convert numeric risk score to human-readable label."""
    if score <= 2:
        return "Low"
    if score <= 4:
        return "Moderate"
    if score <= 6:
        return "Elevated"
    if score <= 8:
        return "High"
    return "Extreme"


def _build_summary(
    score: int,
    label: str,
    vix: float | None,
    sp500_price: float | None,
    sp500_change: float | None,
    sectors: dict[str, float],
) -> str:
    """Generate plain English market risk summary."""
    parts = [f"Market risk is {label.lower()} today (score: {score}/10)."]

    if vix is not None:
        if vix > 30:
            parts.append(f"VIX at {vix:.1f} — elevated fear in the market.")
        elif vix > 20:
            parts.append(f"VIX at {vix:.1f} — above-average uncertainty.")
        elif vix < 15:
            parts.append(f"VIX at {vix:.1f} — markets are calm.")
        else:
            parts.append(f"VIX at {vix:.1f}.")

    if sp500_change is not None:
        direction = "up" if sp500_change > 0 else "down"
        parts.append(
            f"S&P 500 {direction} {abs(sp500_change):.1f}%"
            + (f" at {sp500_price:,.0f}" if sp500_price else "")
            + "."
        )

    # Highlight top and bottom sectors
    if sectors:
        sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_sectors) >= 2:
            best = sorted_sectors[0]
            worst = sorted_sectors[-1]
            parts.append(
                f"Strongest sector: {best[0]} ({'+' if best[1] > 0 else ''}{best[1]:.1f}%). "
                f"Weakest: {worst[0]} ({'+' if worst[1] > 0 else ''}{worst[1]:.1f}%)."
            )

    # Actionable advice based on risk level
    if score <= 3:
        parts.append("Conditions favor taking new positions.")
    elif score <= 5:
        parts.append("Normal conditions — stick to your plan.")
    elif score <= 7:
        parts.append("Exercise caution with new positions. Tighten stop-losses.")
    else:
        parts.append(
            "High-risk environment. Consider reducing exposure and raising cash."
        )

    return " ".join(parts)
