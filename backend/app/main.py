"""
FinCentral API - Main Application

A quantitative stock screening and daily analysis platform for long-term investors.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.core.seed import seed_companies
from app.api.routes import (
    companies_router,
    screener_router,
    daily_brief_router,
    news_router,
    market_router,
    analysis_router,
    portfolio_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting FinCentral API...")
    init_db()
    print("Database initialized")

    # Seed initial company data
    db = SessionLocal()
    try:
        added = seed_companies(db)
        if added > 0:
            print(f"Seeded {added} companies into database")
        else:
            print("Company data already present")
    finally:
        db.close()

    # Start APScheduler for daily analysis
    from app.services.scheduler import configure_scheduler
    sched = configure_scheduler()
    sched.start()
    if settings.daily_analysis_enabled:
        print(
            f"Scheduler started - daily analysis at "
            f"{settings.daily_analysis_hour}:{settings.daily_analysis_minute:02d} AM ET (Mon-Fri)"
        )
    else:
        print("Scheduler started - daily analysis is DISABLED")

    yield

    # Shutdown
    sched.shutdown()
    print("Shutting down FinCentral API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## FinCentral API

    A quantitative stock screening and daily analysis platform.

    ### Features

    - **Daily Pre-Market Brief**: Automated analysis at 6 AM ET with picks, strategies, and news
    - **6 Core Screeners**: Magic Formula, Acquirer's Multiple, F-Score, Z-Score, M-Score, Accrual Ratio
    - **Strategy Engine**: Swing, position, and long-term strategies with plain English rationale
    - **News Integration**: Stock-specific news with sentiment/impact assessment
    - **Market Risk**: Daily 1-10 risk score with VIX, sector performance, and breadth
    - **70+ Fundamental Metrics**: Valuation, profitability, growth, and financial health ratios

    ### Quick Start

    1. Get today's analysis: `GET /api/daily-brief`
    2. Trigger analysis: `POST /api/daily-brief/trigger`
    3. Get stock strategy: `GET /api/analysis/{ticker}/strategy`
    4. Get stock news: `GET /api/news/{ticker}`
    5. Get market risk: `GET /api/market/risk-summary`
    """,
    version=settings.app_version,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies_router, prefix="/api")
app.include_router(screener_router, prefix="/api")
app.include_router(daily_brief_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Welcome to FinCentral API",
        "version": settings.app_version,
        "endpoints": {
            "daily_brief": "/api/daily-brief",
            "companies": "/api/companies",
            "screener": "/api/screener",
            "news": "/api/news",
            "market": "/api/market",
            "analysis": "/api/analysis",
            "portfolio": "/api/portfolio",
            "docs": "/docs",
        },
    }
