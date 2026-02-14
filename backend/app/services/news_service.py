"""
News fetching and sentiment analysis service.
Fetches stock-specific news from FMP, assesses impact using keyword analysis.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models import NewsArticle, DailyPick
from app.services.data_providers import fmp_provider

# Financial keyword lists for sentiment analysis
POSITIVE_KEYWORDS = [
    "beat", "beats", "exceeded", "exceeds", "upgrade", "upgraded", "raise",
    "raises", "raised", "growth", "record", "surge", "surges", "surged",
    "strong", "bullish", "outperform", "buy", "dividend increase",
    "profit", "profitable", "expansion", "deal", "partnership", "approval",
    "breakthrough", "innovation", "milestone", "recovery", "positive",
    "upside", "momentum", "rally", "soar", "gain", "wins",
]

NEGATIVE_KEYWORDS = [
    "miss", "misses", "missed", "downgrade", "downgraded", "cut", "cuts",
    "decline", "declines", "declined", "loss", "losses", "warning", "warns",
    "weak", "bearish", "underperform", "sell", "layoff", "layoffs",
    "recall", "investigation", "lawsuit", "fraud", "bankruptcy", "debt",
    "default", "crash", "plunge", "plunges", "drop", "drops", "slump",
    "negative", "downside", "risk", "concern", "delay", "shortage",
    "fine", "penalty", "scandal", "failure",
]

HIGH_IMPACT_KEYWORDS = [
    "acquisition", "merger", "takeover", "buyout", "spin-off", "ipo",
    "fda approval", "fda rejection", "earnings", "guidance", "forecast",
    "ceo", "board", "sec", "federal reserve", "tariff", "sanctions",
    "bankruptcy", "restructuring", "dividend", "buyback", "split",
]


async def fetch_news_for_picks(db: Session, run_id: int):
    """Fetch news for all stocks that passed today's filters."""
    picks = (
        db.query(DailyPick.ticker)
        .filter(DailyPick.run_id == run_id)
        .distinct()
        .all()
    )
    unique_tickers = [p.ticker for p in picks]

    for ticker in unique_tickers:
        try:
            raw_news = await fmp_provider.get_stock_news(ticker, limit=10)

            for article in raw_news:
                url = article.get("url", "")
                if not url:
                    continue

                # Skip duplicates
                exists = (
                    db.query(NewsArticle.id)
                    .filter(NewsArticle.url == url)
                    .first()
                )
                if exists:
                    continue

                sentiment, impact = _assess_impact(article)
                explanation = _build_impact_explanation(
                    ticker, sentiment, impact, article
                )

                published = _parse_date(article.get("publishedDate"))
                if not published:
                    continue

                news = NewsArticle(
                    ticker=ticker,
                    title=article.get("title", "")[:500],
                    url=url[:1000],
                    source=article.get("site", "")[:200],
                    published_at=published,
                    image_url=article.get("image", "")[:1000] if article.get("image") else None,
                    snippet=(article.get("text", "") or "")[:500],
                    sentiment=sentiment,
                    impact_score=impact,
                    impact_explanation=explanation,
                )
                db.add(news)

        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            continue

    db.commit()


async def fetch_market_news(db: Session):
    """Fetch general market news."""
    try:
        articles = await fmp_provider.get_general_news(page=0, size=20)

        for article in articles:
            url = article.get("link") or article.get("url", "")
            if not url:
                continue

            exists = (
                db.query(NewsArticle.id)
                .filter(NewsArticle.url == url)
                .first()
            )
            if exists:
                continue

            sentiment, impact = _assess_impact(article)
            published = _parse_date(
                article.get("publishedDate") or article.get("date")
            )
            if not published:
                continue

            news = NewsArticle(
                ticker=None,  # General market news
                title=(article.get("title", "") or "")[:500],
                url=url[:1000],
                source=(article.get("site") or article.get("source", ""))[:200],
                published_at=published,
                image_url=article.get("image", "")[:1000] if article.get("image") else None,
                snippet=(article.get("text") or article.get("content", ""))[:500],
                sentiment=sentiment,
                impact_score=impact,
                impact_explanation=_build_impact_explanation(
                    "market", sentiment, impact, article
                ),
            )
            db.add(news)

        db.commit()
    except Exception as e:
        print(f"Error fetching market news: {e}")


def _assess_impact(article: dict) -> tuple[str, float]:
    """
    Rule-based sentiment and impact assessment.

    Analyzes title and snippet for positive/negative financial keywords.
    Returns (sentiment, impact_score) where:
    - sentiment: 'positive', 'negative', or 'neutral'
    - impact_score: -1.0 to 1.0 (magnitude of expected impact)
    """
    text = (
        (article.get("title", "") or "") + " " + (article.get("text", "") or "")
    ).lower()

    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    high_impact = any(kw in text for kw in HIGH_IMPACT_KEYWORDS)

    # Base magnitude from keyword counts
    if pos_count > neg_count:
        base = min(pos_count * 0.15, 0.8)
        if high_impact:
            base = min(base + 0.2, 1.0)
        return "positive", round(base, 2)
    elif neg_count > pos_count:
        base = min(neg_count * 0.15, 0.8)
        if high_impact:
            base = min(base + 0.2, 1.0)
        return "negative", round(-base, 2)

    return "neutral", 0.0


def _build_impact_explanation(
    ticker: str, sentiment: str, impact: float, article: dict
) -> str:
    """Build a plain English explanation of news impact."""
    title = article.get("title", "News article")

    magnitude = abs(impact)
    if magnitude > 0.6:
        strength = "significant"
    elif magnitude > 0.3:
        strength = "moderate"
    elif magnitude > 0:
        strength = "minor"
    else:
        strength = "negligible"

    if sentiment == "positive":
        return (
            f"This news is likely {strength}ly positive for {ticker}. "
            f"Historically, similar positive developments tend to support stock prices "
            f"in the short to medium term."
        )
    elif sentiment == "negative":
        return (
            f"This news could have a {strength} negative impact on {ticker}. "
            f"Similar negative events have historically pressured stock prices. "
            f"Monitor closely for follow-up developments."
        )
    else:
        return (
            f"This news has {strength} expected impact on {ticker}. "
            f"The content appears neutral — no strong directional signal."
        )


def _parse_date(date_str: str | None) -> datetime | None:
    """Parse various date formats from FMP API."""
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue

    return None
