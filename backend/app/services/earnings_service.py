"""
Earnings calendar service.
Fetches upcoming/recent earnings from FMP and tags daily picks
so users know which recommended stocks are about to report.
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import DailyPick, EarningsEvent
from app.services.data_providers import fmp_provider


async def fetch_and_tag_earnings(db: Session, run_id: int):
    """
    Fetch earnings calendar and tag daily picks with earnings proximity.

    Steps:
    1. Fetch earnings calendar from FMP (today-3d to today+14d)
    2. Build ticker → earnings events lookup
    3. Tag DailyPick entries with proximity info
    4. Store EarningsEvent records for reference
    """
    today = date.today()
    from_date = today - timedelta(days=3)
    to_date = today + timedelta(days=14)

    # Fetch earnings calendar from FMP
    raw_events = await fmp_provider.get_earnings_calendar(from_date, to_date)

    if not raw_events:
        return

    # Build lookup: ticker -> list of earnings events
    earnings_lookup: dict[str, list[dict]] = {}
    for event in raw_events:
        ticker = event.get("symbol", "").upper()
        if ticker:
            earnings_lookup.setdefault(ticker, []).append(event)

    # Get daily picks for this run
    picks = db.query(DailyPick).filter(DailyPick.run_id == run_id).all()

    # Delete old earnings events for the date range (allow re-runs)
    db.query(EarningsEvent).filter(
        EarningsEvent.earnings_date >= from_date,
        EarningsEvent.earnings_date <= to_date,
    ).delete(synchronize_session=False)

    stored_tickers = set()

    for pick in picks:
        events = earnings_lookup.get(pick.ticker, [])
        if not events:
            continue

        # Find the most relevant event (closest to today)
        best_event = None
        best_proximity = None

        for event in events:
            earnings_date_str = event.get("date")
            if not earnings_date_str:
                continue

            try:
                earnings_dt = date.fromisoformat(earnings_date_str)
            except (ValueError, TypeError):
                continue

            days_until = (earnings_dt - today).days

            if 0 <= days_until <= 7:
                # Upcoming within 7 days
                if best_proximity != "upcoming_7d" or (
                    best_event and abs(days_until) < abs(
                        (date.fromisoformat(best_event.get("date", "")) - today).days
                    )
                ):
                    best_event = event
                    best_proximity = "upcoming_7d"
            elif -3 <= days_until < 0:
                # Just reported within last 3 days
                if best_proximity is None:
                    best_event = event
                    best_proximity = "just_reported_3d"

        if best_event and best_proximity:
            try:
                pick.earnings_date = date.fromisoformat(best_event["date"])
            except (ValueError, TypeError):
                pass
            pick.earnings_proximity = best_proximity
            eps_est = best_event.get("epsEstimated")
            if eps_est is not None:
                try:
                    pick.eps_estimated = float(eps_est)
                except (ValueError, TypeError):
                    pass

        # Store earnings events for this ticker (once per ticker)
        if pick.ticker not in stored_tickers:
            stored_tickers.add(pick.ticker)
            for event in events:
                earnings_date_str = event.get("date")
                if not earnings_date_str:
                    continue
                try:
                    earnings_dt = date.fromisoformat(earnings_date_str)
                except (ValueError, TypeError):
                    continue

                days_until = (earnings_dt - today).days

                db.add(EarningsEvent(
                    ticker=pick.ticker,
                    earnings_date=earnings_dt,
                    eps_estimated=_safe_float(event.get("epsEstimated")),
                    eps_actual=_safe_float(event.get("eps")),
                    revenue_estimated=_safe_float(event.get("revenueEstimated")),
                    revenue_actual=_safe_float(event.get("revenue")),
                    fiscal_period=event.get("fiscalDateEnding", ""),
                    is_upcoming=days_until >= 0,
                ))

    db.commit()


def _safe_float(val) -> float | None:
    """Convert a value to float safely, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
