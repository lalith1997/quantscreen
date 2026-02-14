"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


# ============== Company Schemas ==============

class CompanyBase(BaseModel):
    """Base company fields."""
    ticker: str
    name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: str = "US"
    currency: str = "USD"


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    market_cap: Optional[int] = None


class CompanyResponse(CompanyBase):
    """Schema for company response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    market_cap: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class CompanyWithMetrics(CompanyResponse):
    """Company with calculated metrics."""
    metrics: dict[str, Any] = Field(default_factory=dict)


# ============== Fundamental Schemas ==============

class FundamentalBase(BaseModel):
    """Base fundamental fields."""
    period_end: date
    period_type: str
    
    # Income Statement
    revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    ebit: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    eps: Optional[Decimal] = None
    eps_diluted: Optional[Decimal] = None
    
    # Balance Sheet
    total_assets: Optional[Decimal] = None
    current_assets: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    current_liabilities: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    shareholders_equity: Optional[Decimal] = None
    cash_and_equivalents: Optional[Decimal] = None
    
    # Cash Flow
    operating_cash_flow: Optional[Decimal] = None
    capital_expenditures: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None


class FundamentalResponse(FundamentalBase):
    """Schema for fundamental response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int
    created_at: datetime


# ============== Price Schemas ==============

class PriceBase(BaseModel):
    """Base price fields."""
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class PriceResponse(PriceBase):
    """Schema for price response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_id: int


# ============== Screener Schemas ==============

class ScreenerFilter(BaseModel):
    """Single filter criterion."""
    metric: str  # e.g., "pe_ratio", "f_score", "magic_formula_rank"
    operator: str  # ">", "<", ">=", "<=", "==", "between", "in"
    value: Any  # number, list of numbers, or list of strings
    percentile: bool = False  # Use percentile instead of absolute
    sector_relative: bool = False  # Compare within sector


class ScreenerRequest(BaseModel):
    """Request to run a screen."""
    filters: list[ScreenerFilter] = Field(default_factory=list)
    logic: str = "AND"  # "AND" or "OR"
    sort_by: str = "market_cap"
    sort_order: str = "desc"  # "asc" or "desc"
    limit: int = 50
    offset: int = 0
    
    # Optional filters
    exclude_sectors: list[str] = Field(default_factory=list)
    min_market_cap: Optional[int] = None
    max_market_cap: Optional[int] = None


class ScreenerResult(BaseModel):
    """Single result from screener."""
    ticker: str
    name: str
    sector: Optional[str]
    market_cap: Optional[int]
    metrics: dict[str, Any]
    rank: int


class ScreenerResponse(BaseModel):
    """Response from running a screen."""
    results: list[ScreenerResult]
    total_count: int
    filters_applied: list[ScreenerFilter]
    execution_time_ms: float


# ============== Screen (Saved) Schemas ==============

class ScreenBase(BaseModel):
    """Base saved screen fields."""
    name: str
    description: Optional[str] = None
    filters: list[ScreenerFilter]
    sort_by: str = "market_cap"
    sort_order: str = "desc"


class ScreenCreate(ScreenBase):
    """Schema for creating a saved screen."""
    pass


class ScreenResponse(ScreenBase):
    """Schema for saved screen response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_preset: bool
    created_at: datetime
    updated_at: datetime


# ============== Watchlist Schemas ==============

class WatchlistBase(BaseModel):
    """Base watchlist fields."""
    name: str
    tickers: list[str] = Field(default_factory=list)


class WatchlistCreate(WatchlistBase):
    """Schema for creating a watchlist."""
    pass


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


# ============== Metric Schemas ==============

class MetricValue(BaseModel):
    """Single calculated metric."""
    name: str
    value: Optional[float]
    rank: Optional[int] = None  # Percentile rank
    category: str  # "valuation", "profitability", "quality", etc.


class CompanyMetrics(BaseModel):
    """All metrics for a company."""
    ticker: str
    name: str
    calculated_at: datetime
    
    # Core Screeners
    magic_formula_rank: Optional[int] = None
    acquirers_multiple: Optional[float] = None
    f_score: Optional[int] = None
    z_score: Optional[float] = None
    m_score: Optional[float] = None
    accrual_ratio: Optional[float] = None
    
    # Valuation Ratios
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    
    # Profitability
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    
    # All metrics as dict for flexibility
    all_metrics: dict[str, Any] = Field(default_factory=dict)


# ============== Health Check ==============

class HealthCheck(BaseModel):
    """API health check response."""
    status: str = "healthy"
    version: str
    database: str = "connected"
