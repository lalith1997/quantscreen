"""
Strategy generation engine.
Produces swing, position, and long-term strategies with plain English rationale.
"""

import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import StockStrategy, DailyPick
from app.services.data_providers import fmp_provider, FMPProvider
from app.services.technical import (
    calculate_rsi,
    calculate_macd,
    calculate_sma,
    calculate_atr,
    find_support_resistance,
)


async def generate_strategies_for_picks(db: Session, run_id: int):
    """Generate swing, position, and long-term strategies for all daily picks."""
    picks = db.query(DailyPick).filter(DailyPick.run_id == run_id).all()
    unique_tickers = list({p.ticker for p in picks})

    # Build a map of ticker -> metrics from picks
    ticker_metrics = {}
    for p in picks:
        if p.ticker not in ticker_metrics:
            ticker_metrics[p.ticker] = p.metrics or {}

    today = date.today()
    semaphore = asyncio.Semaphore(5)

    async def process_ticker(ticker: str):
        async with semaphore:
            try:
                fmp = FMPProvider()
                prices_raw = await fmp.get_historical_prices(
                    ticker,
                    from_date=today - timedelta(days=150),
                    to_date=today,
                )
                await fmp.close()

                if not prices_raw or len(prices_raw) < 30:
                    return []

                # FMP returns newest-first, reverse for chronological
                prices_raw = list(reversed(prices_raw))
                closes = [p["close"] for p in prices_raw]
                highs = [p["high"] for p in prices_raw]
                lows = [p["low"] for p in prices_raw]
                current_price = closes[-1]
                metrics = ticker_metrics.get(ticker, {})

                strategies = []

                swing = _build_swing_strategy(
                    ticker, today, current_price, closes, highs, lows, metrics
                )
                if swing:
                    strategies.append(swing)

                position = _build_position_strategy(
                    ticker, today, current_price, closes, highs, lows, metrics
                )
                if position:
                    strategies.append(position)

                longterm = _build_longterm_strategy(
                    ticker, today, current_price, metrics
                )
                if longterm:
                    strategies.append(longterm)

                return strategies
            except Exception as e:
                print(f"Error generating strategies for {ticker}: {e}")
                return []

    tasks = [process_ticker(t) for t in unique_tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Delete old strategies for today to allow re-runs
    db.query(StockStrategy).filter(
        StockStrategy.analysis_date == today,
        StockStrategy.ticker.in_(unique_tickers),
    ).delete(synchronize_session=False)

    for result in results:
        if isinstance(result, list):
            for strategy in result:
                db.add(strategy)

    db.commit()


def _build_swing_strategy(
    ticker: str,
    today: date,
    price: float,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    metrics: dict,
) -> StockStrategy | None:
    """
    Swing trading strategy (days to weeks).
    Uses RSI, MACD, support/resistance, and ATR for entries and exits.
    """
    rsi = calculate_rsi(closes)
    macd = calculate_macd(closes)
    sr = find_support_resistance(closes)
    atr = calculate_atr(highs, lows, closes)
    sma50 = calculate_sma(closes, 50)

    # Stop-loss: nearest support or 2x ATR below entry
    if sr and sr.get("support"):
        stop_loss = sr["support"]
    elif atr:
        stop_loss = price - (atr * 2)
    else:
        stop_loss = price * 0.95

    # Take-profit: nearest resistance or 2:1 risk-reward
    risk = price - stop_loss
    if risk <= 0:
        risk = price * 0.05
        stop_loss = price - risk

    if sr and sr.get("resistance"):
        take_profit = sr["resistance"]
    else:
        take_profit = price + (risk * 2)

    rr_ratio = (take_profit - price) / risk if risk > 0 else 0

    # Confidence based on signal alignment
    signals = []
    confidence_points = 0

    if rsi is not None:
        if rsi < 30:
            signals.append(f"RSI oversold at {rsi:.0f} — strong buy signal")
            confidence_points += 2
        elif rsi < 45:
            signals.append(f"RSI approaching oversold at {rsi:.0f}")
            confidence_points += 1
        elif rsi > 70:
            signals.append(f"RSI overbought at {rsi:.0f} — caution advised")
        else:
            signals.append(f"RSI neutral at {rsi:.0f}")

    if macd:
        if macd["bullish"]:
            signals.append("MACD histogram positive — bullish momentum")
            confidence_points += 1
        else:
            signals.append("MACD histogram negative — bearish momentum")

    if sma50 is not None:
        if price > sma50:
            signals.append(f"Trading above 50-day SMA (${sma50:.2f}) — uptrend")
            confidence_points += 1
        else:
            signals.append(f"Trading below 50-day SMA (${sma50:.2f}) — downtrend")

    if atr:
        signals.append(f"Average True Range: ${atr:.2f} (daily volatility)")

    confidence = (
        "high" if confidence_points >= 3
        else "medium" if confidence_points >= 2
        else "low"
    )

    rationale_parts = [f"Swing trade setup for {ticker} at ${price:.2f}."]
    rationale_parts.extend(signals)
    rationale_parts.append(
        f"Entry at ${price:.2f}, stop-loss at ${stop_loss:.2f} "
        f"(risking ${risk:.2f}), target ${take_profit:.2f} "
        f"(reward ${take_profit - price:.2f}). "
        f"Risk/reward ratio: 1:{rr_ratio:.1f}."
    )

    return StockStrategy(
        ticker=ticker,
        analysis_date=today,
        timeframe="swing",
        entry_price=round(price, 4),
        stop_loss=round(stop_loss, 4),
        take_profit=round(take_profit, 4),
        risk_reward_ratio=round(rr_ratio, 2),
        confidence=confidence,
        rationale=" ".join(rationale_parts),
        signals={
            "rsi": rsi,
            "macd": macd,
            "support_resistance": sr,
            "sma50": sma50,
            "atr": atr,
        },
    )


def _build_position_strategy(
    ticker: str,
    today: date,
    price: float,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    metrics: dict,
) -> StockStrategy | None:
    """
    Position trading strategy (weeks to months).
    Uses SMA crossovers, fundamentals, and accumulation zones.
    """
    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    rsi = calculate_rsi(closes)

    # Entry: suggest buying on a 3% pullback from current level
    entry = round(price * 0.97, 4)
    stop_loss = round(price * 0.90, 4)  # 10% stop
    take_profit = round(price * 1.20, 4)  # 20% target

    risk = entry - stop_loss
    reward = take_profit - entry
    rr_ratio = reward / risk if risk > 0 else 0

    signals = []
    confidence_points = 0

    if sma20 and sma50:
        if sma20 > sma50:
            signals.append(
                f"20-day SMA (${sma20:.2f}) above 50-day SMA (${sma50:.2f}) — bullish trend confirmed"
            )
            confidence_points += 1
        else:
            signals.append(
                f"20-day SMA (${sma20:.2f}) below 50-day SMA (${sma50:.2f}) — trend is bearish, wait for crossover"
            )

    f_score = metrics.get("f_score")
    if f_score is not None:
        if f_score >= 7:
            signals.append(f"Strong fundamentals with Piotroski F-Score of {f_score}/9")
            confidence_points += 2
        elif f_score >= 5:
            signals.append(f"Decent fundamentals with F-Score of {f_score}/9")
            confidence_points += 1
        else:
            signals.append(f"Weak fundamentals with F-Score of {f_score}/9 — be cautious")

    z_score = metrics.get("z_score")
    if z_score is not None:
        if z_score > 2.99:
            signals.append(f"Financially safe (Altman Z-Score: {z_score:.2f})")
            confidence_points += 1
        elif z_score < 1.81:
            signals.append(f"Bankruptcy risk detected (Z-Score: {z_score:.2f}) — avoid or size small")

    pe = metrics.get("pe_ratio")
    if pe is not None and pe > 0:
        if pe < 15:
            signals.append(f"Attractively valued at P/E {pe:.1f}")
            confidence_points += 1
        elif pe < 25:
            signals.append(f"Fairly valued at P/E {pe:.1f}")
        else:
            signals.append(f"Expensive at P/E {pe:.1f} — wait for better entry")

    confidence = (
        "high" if confidence_points >= 4
        else "medium" if confidence_points >= 2
        else "low"
    )

    rationale_parts = [f"Position trade for {ticker}."]
    rationale_parts.append(
        f"Accumulate near ${entry:.2f} (3% below current price). "
        f"Stop-loss at ${stop_loss:.2f} (10% risk), target ${take_profit:.2f} (20% upside). "
        f"Risk/reward: 1:{rr_ratio:.1f}."
    )
    rationale_parts.extend(signals)

    return StockStrategy(
        ticker=ticker,
        analysis_date=today,
        timeframe="position",
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=round(rr_ratio, 2),
        confidence=confidence,
        rationale=" ".join(rationale_parts),
        signals={
            "sma20": sma20,
            "sma50": sma50,
            "rsi": rsi,
            "f_score": f_score,
            "z_score": z_score,
            "pe_ratio": pe,
        },
    )


def _build_longterm_strategy(
    ticker: str,
    today: date,
    price: float,
    metrics: dict,
) -> StockStrategy | None:
    """
    Long-term investing strategy (months+).
    Focuses on fair value, margin of safety, financial health, and compounding.
    """
    pe = metrics.get("pe_ratio")
    earnings_yield = metrics.get("earnings_yield")
    roe = metrics.get("roe")
    z_score = metrics.get("z_score")
    f_score = metrics.get("f_score")

    # Fair value estimation using earnings yield
    fair_value = None
    margin_of_safety = None
    if earnings_yield and earnings_yield > 0:
        # Implied fair price if market priced at 15x earnings
        implied_eps = price * earnings_yield
        fair_value = round(implied_eps * 15, 2)
        if fair_value > 0:
            margin_of_safety = round(((fair_value - price) / fair_value) * 100, 1)

    entry = round(price, 4)
    stop_loss = round(price * 0.75, 4)  # 25% maximum drawdown tolerance
    take_profit = round(fair_value, 4) if fair_value and fair_value > price else round(price * 1.50, 4)

    signals = []
    confidence_points = 0

    if z_score is not None:
        if z_score > 2.99:
            signals.append(f"Financially safe — Altman Z-Score {z_score:.2f} (well above distress zone)")
            confidence_points += 1
        elif z_score > 1.81:
            signals.append(f"Grey zone — Z-Score {z_score:.2f} (monitor closely)")
        else:
            signals.append(f"Distress zone — Z-Score {z_score:.2f} (high bankruptcy risk)")

    if f_score is not None:
        if f_score >= 7:
            signals.append(f"Excellent financial strength — F-Score {f_score}/9")
            confidence_points += 2
        elif f_score >= 5:
            signals.append(f"Moderate financial strength — F-Score {f_score}/9")
            confidence_points += 1

    if roe is not None:
        if roe > 20:
            signals.append(f"High return on equity: {roe:.1f}% — strong competitive advantage")
            confidence_points += 1
        elif roe > 10:
            signals.append(f"Solid ROE: {roe:.1f}%")

    if margin_of_safety is not None:
        if margin_of_safety > 30:
            signals.append(f"Large margin of safety: {margin_of_safety:.0f}% below estimated fair value")
            confidence_points += 2
        elif margin_of_safety > 10:
            signals.append(f"Moderate margin of safety: {margin_of_safety:.0f}%")
            confidence_points += 1
        elif margin_of_safety < 0:
            signals.append(f"Trading {abs(margin_of_safety):.0f}% above estimated fair value — may be overpriced")

    m_score_flag = metrics.get("m_score_flag")
    if m_score_flag:
        signals.append("Warning: Beneish M-Score flags potential earnings manipulation")

    confidence = (
        "high" if confidence_points >= 4
        else "medium" if confidence_points >= 2
        else "low"
    )

    rationale_parts = [f"Long-term investment case for {ticker} at ${price:.2f}."]
    if fair_value:
        rationale_parts.append(f"Estimated fair value: ${fair_value:.2f}.")
    rationale_parts.append(
        f"Maximum drawdown tolerance: 25% (stop at ${stop_loss:.2f}). "
    )
    rationale_parts.extend(signals)

    return StockStrategy(
        ticker=ticker,
        analysis_date=today,
        timeframe="longterm",
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward_ratio=None,
        confidence=confidence,
        rationale=" ".join(rationale_parts),
        signals={
            "pe": pe,
            "roe": roe,
            "z_score": z_score,
            "f_score": f_score,
            "earnings_yield": earnings_yield,
            "fair_value": fair_value,
            "margin_of_safety": margin_of_safety,
        },
    )
