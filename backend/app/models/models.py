"""
SQLAlchemy database models for QuantScreen.
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Date, DateTime,
    Boolean, ForeignKey, Index, Text, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Company(Base):
    """Master table for all tracked companies."""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(100), index=True)
    industry = Column(String(100))
    market_cap = Column(BigInteger)
    country = Column(String(50), default="US")
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    is_etf = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fundamentals = relationship("Fundamental", back_populates="company", lazy="dynamic")
    prices = relationship("Price", back_populates="company", lazy="dynamic")
    metrics = relationship("MetricCache", back_populates="company", lazy="dynamic")
    
    def __repr__(self):
        return f"<Company {self.ticker}: {self.name}>"


class Fundamental(Base):
    """Quarterly and annual fundamental data."""
    
    __tablename__ = "fundamentals"
    __table_args__ = (
        Index("ix_fundamentals_company_period", "company_id", "period_end", "period_type"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_end = Column(Date, nullable=False)
    period_type = Column(String(10))  # Q1, Q2, Q3, Q4, FY
    
    # Income Statement
    revenue = Column(Numeric(20, 2))
    cost_of_revenue = Column(Numeric(20, 2))
    gross_profit = Column(Numeric(20, 2))
    operating_income = Column(Numeric(20, 2))
    ebit = Column(Numeric(20, 2))
    ebitda = Column(Numeric(20, 2))
    net_income = Column(Numeric(20, 2))
    eps = Column(Numeric(12, 4))
    eps_diluted = Column(Numeric(12, 4))
    
    # Balance Sheet
    total_assets = Column(Numeric(20, 2))
    current_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    current_liabilities = Column(Numeric(20, 2))
    total_debt = Column(Numeric(20, 2))
    long_term_debt = Column(Numeric(20, 2))
    shareholders_equity = Column(Numeric(20, 2))
    retained_earnings = Column(Numeric(20, 2))
    cash_and_equivalents = Column(Numeric(20, 2))
    
    # Additional Balance Sheet items for formulas
    net_receivables = Column(Numeric(20, 2))
    inventory = Column(Numeric(20, 2))
    property_plant_equipment = Column(Numeric(20, 2))
    intangible_assets = Column(Numeric(20, 2))
    goodwill = Column(Numeric(20, 2))
    
    # Cash Flow
    operating_cash_flow = Column(Numeric(20, 2))
    capital_expenditures = Column(Numeric(20, 2))
    free_cash_flow = Column(Numeric(20, 2))
    dividends_paid = Column(Numeric(20, 2))
    depreciation_amortization = Column(Numeric(20, 2))
    
    # Shares
    shares_outstanding = Column(BigInteger)
    shares_outstanding_diluted = Column(BigInteger)
    
    # SG&A and other expenses (for M-Score)
    sga_expense = Column(Numeric(20, 2))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="fundamentals")
    
    def __repr__(self):
        return f"<Fundamental {self.company_id} {self.period_end} {self.period_type}>"


class Price(Base):
    """Daily OHLCV price data."""
    
    __tablename__ = "prices"
    __table_args__ = (
        Index("ix_prices_company_date", "company_id", "date"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    adjusted_close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    
    # Relationships
    company = relationship("Company", back_populates="prices")
    
    def __repr__(self):
        return f"<Price {self.company_id} {self.date}: {self.close}>"


class MetricCache(Base):
    """Cached calculated metrics for faster screening."""
    
    __tablename__ = "metrics_cache"
    __table_args__ = (
        Index("ix_metrics_company_name", "company_id", "metric_name"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(20, 6))
    rank_value = Column(Integer)  # Percentile rank 1-100
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="metrics")
    
    def __repr__(self):
        return f"<Metric {self.company_id} {self.metric_name}: {self.metric_value}>"


class Screen(Base):
    """Saved screening configurations."""
    
    __tablename__ = "screens"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    filters = Column(JSON, nullable=False)  # Screening criteria
    sort_by = Column(String(100), default="market_cap")
    sort_order = Column(String(10), default="desc")
    is_preset = Column(Boolean, default=False)  # Built-in screens
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Screen {self.name}>"


class Watchlist(Base):
    """User watchlists."""
    
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tickers = Column(JSON, default=list)  # List of ticker symbols
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Watchlist {self.name}>"


class DailyAnalysisRun(Base):
    """Metadata for each daily analysis execution."""

    __tablename__ = "daily_analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(Date, nullable=False, unique=True, index=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    stocks_analyzed = Column(Integer, default=0)
    stocks_passed = Column(Integer, default=0)
    status = Column(String(20), default="running")  # running, completed, failed
    error_message = Column(Text)
    execution_time_seconds = Column(Numeric(10, 2))

    picks = relationship("DailyPick", back_populates="run", lazy="dynamic")

    def __repr__(self):
        return f"<DailyAnalysisRun {self.run_date} {self.status}>"


class DailyPick(Base):
    """Stocks that passed filter presets for a given analysis run."""

    __tablename__ = "daily_picks"
    __table_args__ = (
        Index("ix_daily_picks_run_ticker", "run_id", "ticker"),
    )

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("daily_analysis_runs.id"), nullable=False)
    ticker = Column(String(20), nullable=False, index=True)
    screen_name = Column(String(100), nullable=False)
    metrics = Column(JSON)
    rank = Column(Integer)
    rationale = Column(Text)

    run = relationship("DailyAnalysisRun", back_populates="picks")

    def __repr__(self):
        return f"<DailyPick {self.ticker} #{self.rank} ({self.screen_name})>"


class StockStrategy(Base):
    """Strategy recommendation per stock per timeframe."""

    __tablename__ = "stock_strategies"
    __table_args__ = (
        Index("ix_strategies_ticker_date", "ticker", "analysis_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    analysis_date = Column(Date, nullable=False)
    timeframe = Column(String(20), nullable=False)  # swing, position, longterm

    entry_price = Column(Numeric(12, 4))
    stop_loss = Column(Numeric(12, 4))
    take_profit = Column(Numeric(12, 4))
    risk_reward_ratio = Column(Numeric(6, 2))
    confidence = Column(String(10))  # high, medium, low

    rationale = Column(Text)
    signals = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StockStrategy {self.ticker} {self.timeframe} {self.analysis_date}>"


class NewsArticle(Base):
    """Fetched news articles with impact assessment."""

    __tablename__ = "news_articles"
    __table_args__ = (
        Index("ix_news_ticker_date", "ticker", "published_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(200))
    published_at = Column(DateTime, nullable=False, index=True)
    image_url = Column(String(1000))
    snippet = Column(Text)

    sentiment = Column(String(10))  # positive, negative, neutral
    impact_score = Column(Numeric(4, 2))  # -1.0 to 1.0
    impact_explanation = Column(Text)

    fetched_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewsArticle {self.ticker} {self.title[:30]}>"


class MarketRiskSnapshot(Base):
    """Daily market conditions summary."""

    __tablename__ = "market_risk_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)

    risk_score = Column(Integer)  # 1-10
    risk_label = Column(String(20))  # Low, Moderate, Elevated, High, Extreme

    vix_level = Column(Numeric(8, 2))
    sp500_price = Column(Numeric(12, 4))
    sp500_change_pct = Column(Numeric(6, 2))

    sector_data = Column(JSON)
    breadth_data = Column(JSON)

    summary_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketRiskSnapshot {self.snapshot_date} risk={self.risk_score}>"
