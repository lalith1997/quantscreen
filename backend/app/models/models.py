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
