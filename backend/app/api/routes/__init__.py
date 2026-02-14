"""API routes."""

from app.api.routes.companies import router as companies_router
from app.api.routes.screener import router as screener_router
from app.api.routes.daily_brief import router as daily_brief_router
from app.api.routes.news import router as news_router
from app.api.routes.market import router as market_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.portfolio import router as portfolio_router

__all__ = [
    "companies_router",
    "screener_router",
    "daily_brief_router",
    "news_router",
    "market_router",
    "analysis_router",
    "portfolio_router",
]
