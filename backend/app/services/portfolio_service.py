"""
Portfolio tracking and health monitoring service.
Enriches holdings with live prices, runs health checks,
and generates alerts using plain English at a college-student reading level.
"""

import asyncio
import csv
import io
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import (
    PortfolioHolding,
    PortfolioSnapshot,
    PortfolioAlert,
    EarningsEvent,
)
from app.services.data_providers import YFinanceProvider
from app.services.formula_engine import FormulaEngine
from app.services.technical import calculate_rsi, calculate_macd, calculate_sma
from app.services.rationale_helpers import explain_metric


async def get_holdings_with_prices(db: Session) -> list[dict]:
    """
    Fetch all active holdings, enrich with current quote
    (price, change %), and calculate P&L.
    """
    holdings = (
        db.query(PortfolioHolding)
        .filter(PortfolioHolding.is_active == True)
        .all()
    )

    if not holdings:
        return []

    yf_prov = YFinanceProvider()
    results = []

    for h in holdings:
        try:
            quote = await yf_prov.get_quote(h.ticker)
            current_price = quote.get("price") if quote else None
            change_pct = quote.get("changesPercentage") if quote else None

            shares = float(h.shares)
            cost_basis = float(h.avg_cost_basis)
            market_value = shares * current_price if current_price else None
            total_cost = shares * cost_basis
            gain_loss = (market_value - total_cost) if market_value else None
            gain_loss_pct = (
                ((current_price - cost_basis) / cost_basis) * 100
                if current_price and cost_basis > 0
                else None
            )

            results.append({
                "id": h.id,
                "ticker": h.ticker,
                "shares": shares,
                "avg_cost_basis": cost_basis,
                "buy_date": h.buy_date.isoformat() if h.buy_date else None,
                "notes": h.notes,
                "is_active": h.is_active,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "current_price": current_price,
                "market_value": round(market_value, 2) if market_value else None,
                "gain_loss": round(gain_loss, 2) if gain_loss else None,
                "gain_loss_pct": round(gain_loss_pct, 2) if gain_loss_pct else None,
                "todays_change_pct": change_pct,
            })
        except Exception as e:
            print(f"Error enriching holding {h.ticker}: {e}")
            results.append({
                "id": h.id,
                "ticker": h.ticker,
                "shares": float(h.shares),
                "avg_cost_basis": float(h.avg_cost_basis),
                "buy_date": h.buy_date.isoformat() if h.buy_date else None,
                "notes": h.notes,
                "is_active": h.is_active,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "current_price": None,
                "market_value": None,
                "gain_loss": None,
                "gain_loss_pct": None,
                "todays_change_pct": None,
            })

    await yf_prov.close()
    return results


async def run_portfolio_analysis(db: Session):
    """
    Full portfolio health check.
    1. For each holding: fetch fundamentals + calculate F-Score, Z-Score, M-Score
    2. Fetch 150d prices -> RSI, MACD, SMA50
    3. Generate alerts based on thresholds
    4. Create PortfolioSnapshot with per-holding detail
    """
    holdings = (
        db.query(PortfolioHolding)
        .filter(PortfolioHolding.is_active == True)
        .all()
    )

    if not holdings:
        return

    today = date.today()

    # Clear old alerts (keep history but don't re-alert same things)
    db.query(PortfolioAlert).filter(
        PortfolioAlert.is_read == False,
    ).delete(synchronize_session=False)

    total_value = 0.0
    total_cost = 0.0
    holdings_data = {}
    new_alerts = []

    semaphore = asyncio.Semaphore(3)

    async def analyze_holding(holding: PortfolioHolding):
        nonlocal total_value, total_cost

        async with semaphore:
            try:
                yf_prov = YFinanceProvider()
                ticker = holding.ticker
                shares = float(holding.shares)
                cost_basis = float(holding.avg_cost_basis)

                # Get quote
                quote = await yf_prov.get_quote(ticker)
                current_price = quote.get("price") if quote else None

                if not current_price:
                    await yf_prov.close()
                    return

                market_val = shares * current_price
                cost_val = shares * cost_basis
                total_value += market_val
                total_cost += cost_val

                # Get fundamentals
                f_score = None
                z_score = None
                m_score_flag = None
                try:
                    data = await yf_prov.build_fundamental_data(ticker)
                    if data:
                        formulas = FormulaEngine.calculate_all(data)
                        if formulas.get("piotroski"):
                            f_score = formulas["piotroski"]["f_score"]
                        if formulas.get("altman_z"):
                            z_score = formulas["altman_z"]["z_score"]
                        if formulas.get("beneish_m"):
                            m_score_flag = formulas["beneish_m"]["is_red_flag"]
                except Exception as e:
                    print(f"  Portfolio fundamentals error for {ticker}: {e}")

                # Get technical indicators
                rsi_val = None
                macd_val = None
                sma50_val = None
                try:
                    prices_raw = await yf_prov.get_historical_prices(
                        ticker,
                        from_date=today - timedelta(days=150),
                        to_date=today,
                    )
                    if prices_raw and len(prices_raw) >= 30:
                        prices_raw = list(reversed(prices_raw))
                        closes = [p["close"] for p in prices_raw]
                        rsi_val = calculate_rsi(closes)
                        macd_val = calculate_macd(closes)
                        sma50_val = calculate_sma(closes, 50)
                except Exception as e:
                    print(f"  Portfolio technicals error for {ticker}: {e}")

                await yf_prov.close()

                # Store holding detail
                gain_loss_pct = ((current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
                holdings_data[ticker] = {
                    "current_price": current_price,
                    "shares": shares,
                    "market_value": round(market_val, 2),
                    "cost_basis": cost_basis,
                    "gain_loss": round(market_val - cost_val, 2),
                    "gain_loss_pct": round(gain_loss_pct, 2),
                    "f_score": f_score,
                    "z_score": round(z_score, 2) if z_score else None,
                    "m_score_flag": m_score_flag,
                    "rsi": round(rsi_val, 1) if rsi_val else None,
                    "sma50": round(sma50_val, 2) if sma50_val else None,
                    "trend": "up" if (sma50_val and current_price > sma50_val) else "down" if sma50_val else None,
                }

                # ===== Generate Alerts =====

                # Exit signals (high severity)
                if rsi_val is not None and rsi_val > 75:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="exit_signal",
                        severity="high",
                        message=(
                            f"{ticker} is very overheated right now (momentum score: "
                            f"{rsi_val:.0f}/100). The price has run up a lot recently. "
                            f"You might want to think about taking some profits before it pulls back."
                        ),
                    ))

                if sma50_val and current_price < sma50_val:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="exit_signal",
                        severity="high",
                        message=(
                            f"{ticker} just dropped below its 50-day average price "
                            f"(${sma50_val:.2f}). That means the overall trend has turned "
                            f"negative. Keep a close eye on this — it could keep falling."
                        ),
                    ))

                if f_score is not None and f_score < 4:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="exit_signal",
                        severity="high",
                        message=(
                            f"{ticker}'s financial health score is only {f_score}/9. "
                            f"That's pretty bad — the company's finances are struggling. "
                            f"You might want to reconsider holding this one."
                        ),
                    ))

                if z_score is not None and z_score < 1.81:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="exit_signal",
                        severity="high",
                        message=(
                            f"{ticker}'s bankruptcy risk score is {z_score:.2f}, which is "
                            f"in the danger zone. This company is at higher risk of "
                            f"financial trouble. Seriously consider selling."
                        ),
                    ))

                if m_score_flag:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="exit_signal",
                        severity="high",
                        message=(
                            f"Warning: {ticker}'s financial statements show signs of "
                            f"possible earnings manipulation. The numbers look suspicious. "
                            f"This is a red flag — be very careful."
                        ),
                    ))

                # Health warnings (medium severity)
                if f_score is not None and 4 <= f_score <= 5:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="health_warning",
                        severity="medium",
                        message=(
                            f"{ticker}'s financial health score is {f_score}/9 — "
                            f"showing some weakness. Not terrible, but there are a "
                            f"few yellow flags. Worth keeping an eye on."
                        ),
                    ))

                if z_score is not None and 1.81 <= z_score <= 2.99:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="health_warning",
                        severity="medium",
                        message=(
                            f"{ticker}'s bankruptcy risk score is {z_score:.2f}, which is "
                            f"in a grey area. Not dangerous yet, but not super safe either. "
                            f"Keep watching it."
                        ),
                    ))

                # Earnings alerts (medium severity)
                upcoming_earnings = (
                    db.query(EarningsEvent)
                    .filter(
                        EarningsEvent.ticker == ticker,
                        EarningsEvent.earnings_date >= today,
                        EarningsEvent.earnings_date <= today + timedelta(days=7),
                    )
                    .first()
                )
                if upcoming_earnings:
                    new_alerts.append(PortfolioAlert(
                        ticker=ticker,
                        alert_type="earnings_alert",
                        severity="medium",
                        message=(
                            f"Heads up: {ticker} is reporting earnings on "
                            f"{upcoming_earnings.earnings_date.strftime('%B %d')}. "
                            f"Earnings can cause big price swings — be prepared for "
                            f"the stock to move either way."
                        ),
                    ))

            except Exception as e:
                print(f"  Error analyzing portfolio holding {holding.ticker}: {e}")

    tasks = [analyze_holding(h) for h in holdings]
    await asyncio.gather(*tasks, return_exceptions=True)

    # Create snapshot
    total_gain_loss = total_value - total_cost
    total_gain_loss_pct = (
        (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
    )

    snapshot = PortfolioSnapshot(
        snapshot_date=today,
        total_value=round(total_value, 2),
        total_cost=round(total_cost, 2),
        total_gain_loss=round(total_gain_loss, 2),
        total_gain_loss_pct=round(total_gain_loss_pct, 2),
        holdings_data=holdings_data,
    )
    db.add(snapshot)

    # Store alerts
    for alert in new_alerts:
        db.add(alert)

    db.commit()
    print(f"  Portfolio analysis: {len(holdings)} holdings, {len(new_alerts)} alerts")


def parse_csv_holdings(csv_content: str) -> list[dict]:
    """
    Parse CSV with flexible column names.
    Supports: ticker, shares, avg_cost/avg_cost_basis/cost, buy_date/date, notes
    Returns list of dicts ready for PortfolioHoldingCreate.
    """
    reader = csv.DictReader(io.StringIO(csv_content))

    # Normalize column names
    column_map = {}
    if reader.fieldnames:
        for col in reader.fieldnames:
            lower = col.strip().lower().replace(" ", "_")
            if lower in ("ticker", "symbol", "stock"):
                column_map[col] = "ticker"
            elif lower in ("shares", "quantity", "qty"):
                column_map[col] = "shares"
            elif lower in ("avg_cost", "avg_cost_basis", "cost", "price", "cost_basis", "avg_price"):
                column_map[col] = "avg_cost_basis"
            elif lower in ("buy_date", "date", "purchase_date"):
                column_map[col] = "buy_date"
            elif lower in ("notes", "note", "comment", "comments"):
                column_map[col] = "notes"

    results = []
    for row in reader:
        mapped = {}
        for orig_col, target_col in column_map.items():
            val = row.get(orig_col, "").strip()
            if val:
                mapped[target_col] = val

        # Validate required fields
        if "ticker" not in mapped or "shares" not in mapped or "avg_cost_basis" not in mapped:
            continue

        try:
            entry = {
                "ticker": mapped["ticker"].upper(),
                "shares": float(mapped["shares"]),
                "avg_cost_basis": float(mapped["avg_cost_basis"]),
            }
            if "buy_date" in mapped:
                entry["buy_date"] = mapped["buy_date"]
            if "notes" in mapped:
                entry["notes"] = mapped["notes"]
            results.append(entry)
        except (ValueError, TypeError):
            continue

    return results
