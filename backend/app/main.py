"""
QuantScreen API - Main Application

A quantitative stock screening platform for long-term investors.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import companies_router, screener_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting QuantScreen API...")
    init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down QuantScreen API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## QuantScreen API
    
    A quantitative stock screening and research platform.
    
    ### Features
    
    - **6 Core Screeners**: Magic Formula, Acquirer's Multiple, F-Score, Z-Score, M-Score, Accrual Ratio
    - **70+ Fundamental Metrics**: Valuation, profitability, growth, and financial health ratios
    - **Pre-built Screens**: Run proven investment strategies with one click
    - **Custom Screening**: Build your own screens with any combination of filters
    
    ### Quick Start
    
    1. Get a company's metrics: `GET /api/companies/{ticker}/metrics`
    2. Run a preset screen: `POST /api/screener/presets/magic_formula/run`
    3. Build custom screens: `POST /api/screener/run`
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
        "message": "Welcome to QuantScreen API",
        "version": settings.app_version,
        "endpoints": {
            "companies": "/api/companies",
            "screener": "/api/screener",
            "docs": "/docs",
        },
    }
