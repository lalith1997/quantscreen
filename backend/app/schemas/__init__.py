"""Pydantic schemas for request/response validation."""

from app.schemas.schemas import (
    # Company
    CompanyBase,
    CompanyCreate,
    CompanyResponse,
    CompanyWithMetrics,

    # Fundamentals
    FundamentalBase,
    FundamentalResponse,

    # Prices
    PriceBase,
    PriceResponse,

    # Screener
    ScreenerFilter,
    ScreenerRequest,
    ScreenerResult,
    ScreenerResponse,

    # Saved Screens
    ScreenBase,
    ScreenCreate,
    ScreenResponse,

    # Watchlist
    WatchlistBase,
    WatchlistCreate,
    WatchlistResponse,

    # Metrics
    MetricValue,
    CompanyMetrics,

    # Daily Brief
    DailyBriefResponse,
    DailyPickResponse,
    EarningsEventResponse,
    StrategyResponse,
    StockStrategyResponse,
    NewsArticleResponse,
    MarketRiskResponse,

    # Portfolio
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
    PortfolioHoldingResponse,
    PortfolioAlertResponse,
    PortfolioSnapshotResponse,

    # Health
    HealthCheck,
)

__all__ = [
    "CompanyBase",
    "CompanyCreate",
    "CompanyResponse",
    "CompanyWithMetrics",
    "FundamentalBase",
    "FundamentalResponse",
    "PriceBase",
    "PriceResponse",
    "ScreenerFilter",
    "ScreenerRequest",
    "ScreenerResult",
    "ScreenerResponse",
    "ScreenBase",
    "ScreenCreate",
    "ScreenResponse",
    "WatchlistBase",
    "WatchlistCreate",
    "WatchlistResponse",
    "MetricValue",
    "CompanyMetrics",
    "DailyBriefResponse",
    "DailyPickResponse",
    "EarningsEventResponse",
    "StrategyResponse",
    "StockStrategyResponse",
    "NewsArticleResponse",
    "MarketRiskResponse",
    "PortfolioHoldingCreate",
    "PortfolioHoldingUpdate",
    "PortfolioHoldingResponse",
    "PortfolioAlertResponse",
    "PortfolioSnapshotResponse",
    "HealthCheck",
]
