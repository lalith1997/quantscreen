"""
Plain-English metric explanations for non-technical users.
Used by daily_engine, strategy_engine, portfolio_service, and news_service.

All language targets a college-student reading level —
no financial jargon without an immediate plain-English explanation.
"""


def explain_metric(name: str, value) -> str:
    """
    Convert any financial metric into a one-liner a college student
    would understand. Returns empty string if metric is unknown or value is None.
    """
    if value is None:
        return ""

    explanations = {
        "earnings_yield": lambda v: (
            f"For every $1 you'd pay for this stock, the company earns about "
            f"{v * 100:.0f} cents per year — "
            + (
                "that's a great deal."
                if v > 0.10
                else "that's a decent return."
                if v > 0.05
                else "that's on the low side."
            )
        ),
        "return_on_capital": lambda v: (
            f"For every dollar the business has invested, it earns "
            f"{v * 100:.0f} cents back. "
            + (
                "That's very efficient."
                if v > 0.20
                else "That's respectable."
                if v > 0.10
                else "That's below average."
            )
        ),
        "f_score": lambda v: (
            f"Financial health score: {int(v)} out of 9. "
            + (
                "Rock solid — this company is in great shape."
                if v >= 8
                else "Healthy — most things look good."
                if v >= 6
                else "Showing some weakness — a few yellow flags."
                if v >= 4
                else "Concerning — the company's finances are struggling."
            )
        ),
        "z_score": lambda v: (
            f"Bankruptcy risk score: {v:.2f}. "
            + (
                "Very safe — this company is financially strong."
                if v > 2.99
                else "In a grey area — not dangerous yet, but worth watching."
                if v > 1.81
                else "In the danger zone — high risk of financial trouble."
            )
        ),
        "pe_ratio": lambda v: (
            f"You're paying ${v:.0f} for every $1 of profit. "
            + (
                "That's a bargain."
                if v < 12
                else "That's reasonable."
                if v < 20
                else "That's on the pricey side."
                if v < 35
                else "That's very expensive."
            )
        ),
        "acquirers_multiple": lambda v: (
            f"If someone bought this entire company, they'd pay {v:.1f}x "
            f"its yearly operating profits. "
            + (
                "A deep discount."
                if v < 5
                else "A good deal."
                if v < 8
                else "Fair price."
                if v < 12
                else "Expensive."
            )
        ),
        "roe": lambda v: (
            f"The company turns shareholders' money into {v:.0f}% profit per year. "
            + (
                "Outstanding — this is a money-making machine."
                if v > 25
                else "Strong — above average."
                if v > 15
                else "Average."
                if v > 8
                else "Below average."
            )
        ),
        "rsi": lambda v: (
            f"Momentum reading: {v:.0f} out of 100. "
            + (
                "The stock has been beaten down a lot recently — like a sale at the store."
                if v < 30
                else "It's getting close to cheap territory."
                if v < 45
                else "Normal range — nothing extreme."
                if v < 60
                else "Getting hot — lots of buying recently."
                if v < 70
                else "Overheated — the price has run up a lot. Could pull back."
            )
        ),
        "m_score_flag": lambda v: (
            "Warning: the numbers suggest the company might be inflating "
            "its earnings — the books look suspicious."
            if v
            else "No signs of earnings manipulation — the books look clean."
        ),
        "accrual_ratio": lambda v: (
            f"Earnings quality: "
            + (
                "Very high quality — profits are backed by real cash."
                if v < -10
                else "Good quality."
                if v < 5
                else "Moderate quality — some profits are just accounting, not cash."
                if v < 10
                else "Red flag — a lot of the reported profit isn't real cash."
            )
        ),
    }

    fn = explanations.get(name)
    if fn is not None:
        try:
            return fn(value)
        except (TypeError, ValueError):
            return ""
    return ""


def plain_signal(indicator: str, value, context: dict | None = None) -> str:
    """
    Convert a technical indicator signal into plain English.
    Used by strategy_engine for signal descriptions.
    """
    if indicator == "rsi":
        if value is None:
            return ""
        v = value
        if v < 30:
            return (
                f"This stock has been beaten down recently (momentum score: "
                f"{v:.0f}/100) — think of it like a clearance sale. "
                f"Buyers often step in at these levels."
            )
        elif v < 45:
            return (
                f"The stock is approaching cheap territory "
                f"(momentum score: {v:.0f}/100)."
            )
        elif v > 70:
            return (
                f"The stock is overheated (momentum score: {v:.0f}/100) — "
                f"it's run up a lot recently. Be careful buying at these levels."
            )
        else:
            return f"Momentum is in a normal range ({v:.0f}/100) — no extremes."

    elif indicator == "macd":
        if value is None:
            return ""
        if isinstance(value, dict):
            bullish = value.get("bullish", False)
        else:
            bullish = value
        if bullish:
            return (
                "The momentum is turning positive — buyers are stepping "
                "back in and pushing the price higher."
            )
        else:
            return (
                "The momentum is negative — sellers are in control "
                "and the price has been drifting lower."
            )

    elif indicator == "sma50":
        if value is None or context is None:
            return ""
        price = context.get("price")
        if price is None:
            return ""
        if price > value:
            return (
                f"The price is above its 50-day average (${value:.2f}), "
                f"which means the overall trend has been going up."
            )
        else:
            return (
                f"The price is below its 50-day average (${value:.2f}), "
                f"which means the overall trend has been going down."
            )

    elif indicator == "sma_crossover":
        sma20 = context.get("sma20") if context else None
        sma50 = context.get("sma50") if context else None
        if sma20 is None or sma50 is None:
            return ""
        if sma20 > sma50:
            return (
                f"The short-term trend (${sma20:.2f}) is above the "
                f"longer-term trend (${sma50:.2f}) — that's a positive "
                f"sign that the stock is gaining strength."
            )
        else:
            return (
                f"The short-term trend (${sma20:.2f}) is below the "
                f"longer-term trend (${sma50:.2f}) — that's a warning "
                f"sign. The stock might keep falling. Wait for things "
                f"to turn around."
            )

    elif indicator == "atr":
        if value is None:
            return ""
        volatility_note = (
            "That's pretty volatile — expect big swings."
            if value > 5
            else "That's moderate movement."
        )
        return (
            f"This stock typically moves about ${value:.2f} per day. "
            f"{volatility_note}"
        )

    return ""
