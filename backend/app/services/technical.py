"""
Technical indicator calculations for strategy generation.
Uses price history to compute RSI, MACD, SMA, ATR, and support/resistance levels.
"""

from typing import Optional


def calculate_rsi(prices: list[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index.
    RSI < 30 = oversold, RSI > 70 = overbought.
    """
    if len(prices) < period + 1:
        return None

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    recent = deltas[-period:]
    gains = [d if d > 0 else 0 for d in recent]
    losses = [-d if d < 0 else 0 for d in recent]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _ema(values: list[float], period: int) -> list[float]:
    """Calculate exponential moving average series."""
    if len(values) < period:
        return []
    multiplier = 2 / (period + 1)
    ema_values = [sum(values[:period]) / period]
    for val in values[period:]:
        ema_values.append((val - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def calculate_macd(prices: list[float]) -> Optional[dict]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    MACD Line = EMA(12) - EMA(26)
    Signal Line = EMA(9) of MACD Line
    Histogram = MACD Line - Signal Line
    """
    if len(prices) < 35:  # Need at least 26 + 9 periods
        return None

    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)

    # Align EMA series (ema26 starts later)
    offset = len(ema12) - len(ema26)
    macd_line = [ema12[i + offset] - ema26[i] for i in range(len(ema26))]

    if len(macd_line) < 9:
        return None

    signal = _ema(macd_line, 9)
    if not signal:
        return None

    offset2 = len(macd_line) - len(signal)
    histogram = macd_line[-1] - signal[-1]

    return {
        "macd_line": round(macd_line[-1], 4),
        "signal_line": round(signal[-1], 4),
        "histogram": round(histogram, 4),
        "bullish": histogram > 0,
    }


def calculate_sma(prices: list[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 4)


def calculate_atr(
    highs: list[float], lows: list[float], closes: list[float], period: int = 14
) -> Optional[float]:
    """
    Calculate Average True Range.
    Used for stop-loss sizing - higher ATR = more volatile = wider stops needed.
    """
    if len(closes) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    return round(sum(true_ranges[-period:]) / period, 4)


def find_support_resistance(
    prices: list[float], window: int = 20
) -> Optional[dict]:
    """
    Find nearest support and resistance levels using local min/max.
    Scans for pivot points in recent price history.
    """
    if len(prices) < window * 2:
        return None

    current = prices[-1]
    supports = []
    resistances = []

    # Look for local minima (support) and maxima (resistance)
    for i in range(window, len(prices) - window):
        segment = prices[i - window : i + window + 1]
        mid = prices[i]

        if mid == min(segment):
            supports.append(mid)
        elif mid == max(segment):
            resistances.append(mid)

    # Find nearest support below current price
    support_levels = [s for s in supports if s < current]
    resistance_levels = [r for r in resistances if r > current]

    result = {}
    if support_levels:
        result["support"] = round(max(support_levels), 4)  # Nearest support below
    if resistance_levels:
        result["resistance"] = round(min(resistance_levels), 4)  # Nearest resistance above

    return result if result else None
