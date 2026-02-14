"""
Company API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models import Company
from app.schemas import CompanyResponse, CompanyWithMetrics
from app.services.data_providers import fmp_provider
from app.services.formula_engine import FormulaEngine

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    sector: Optional[str] = None,
    country: str = "US",
    min_market_cap: Optional[int] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List all companies with optional filters.
    """
    query = db.query(Company).filter(Company.is_active == True)
    
    if sector:
        query = query.filter(Company.sector == sector)
    if country:
        query = query.filter(Company.country == country)
    if min_market_cap:
        query = query.filter(Company.market_cap >= min_market_cap)
    
    companies = query.order_by(Company.market_cap.desc()).offset(offset).limit(limit).all()
    return companies


@router.get("/search")
async def search_companies(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """
    Search companies by ticker or name.
    """
    query = db.query(Company).filter(
        Company.is_active == True,
        (Company.ticker.ilike(f"%{q}%")) | (Company.name.ilike(f"%{q}%"))
    )
    
    companies = query.order_by(Company.market_cap.desc()).limit(limit).all()
    return [{"ticker": c.ticker, "name": c.name, "sector": c.sector} for c in companies]


@router.get("/sectors")
async def list_sectors(db: Session = Depends(get_db)):
    """
    Get list of unique sectors.
    """
    sectors = db.query(Company.sector).distinct().filter(
        Company.sector.isnot(None),
        Company.is_active == True
    ).all()
    return [s[0] for s in sectors if s[0]]


@router.get("/{ticker}", response_model=CompanyWithMetrics)
async def get_company(ticker: str, db: Session = Depends(get_db)):
    """
    Get company details with calculated metrics.
    """
    company = db.query(Company).filter(
        Company.ticker == ticker.upper(),
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
    
    # Fetch live data and calculate metrics
    fundamental_data = await fmp_provider.build_fundamental_data(ticker.upper())
    
    metrics = {}
    if fundamental_data:
        all_formulas = FormulaEngine.calculate_all(fundamental_data)
        valuation = FormulaEngine.calculate_valuation_ratios(fundamental_data)
        
        # Flatten metrics for response
        if all_formulas.get("piotroski"):
            metrics["f_score"] = all_formulas["piotroski"]["f_score"]
        if all_formulas.get("acquirers_multiple"):
            metrics["acquirers_multiple"] = all_formulas["acquirers_multiple"]
        if all_formulas.get("altman_z"):
            metrics["z_score"] = all_formulas["altman_z"]["z_score"]
        if all_formulas.get("beneish_m"):
            metrics["m_score"] = all_formulas["beneish_m"]["m_score"]
            metrics["m_score_flag"] = all_formulas["beneish_m"]["is_red_flag"]
        if all_formulas.get("sloan_accrual"):
            metrics["accrual_ratio"] = all_formulas["sloan_accrual"]["accrual_ratio_pct"]
        
        metrics.update(valuation)
    
    return CompanyWithMetrics(
        id=company.id,
        ticker=company.ticker,
        name=company.name,
        exchange=company.exchange,
        sector=company.sector,
        industry=company.industry,
        market_cap=company.market_cap,
        country=company.country,
        currency=company.currency,
        is_active=company.is_active,
        created_at=company.created_at,
        updated_at=company.updated_at,
        metrics=metrics,
    )


@router.get("/{ticker}/fundamentals")
async def get_fundamentals(ticker: str):
    """
    Get fundamental data for a company from FMP.
    """
    income = await fmp_provider.get_income_statement(ticker.upper(), "annual", 5)
    balance = await fmp_provider.get_balance_sheet(ticker.upper(), "annual", 5)
    cashflow = await fmp_provider.get_cash_flow_statement(ticker.upper(), "annual", 5)
    
    if not income and not balance:
        raise HTTPException(status_code=404, detail=f"No fundamental data for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "income_statements": income,
        "balance_sheets": balance,
        "cash_flow_statements": cashflow,
    }


@router.get("/{ticker}/metrics")
async def get_metrics(ticker: str):
    """
    Calculate all metrics for a company.
    """
    fundamental_data = await fmp_provider.build_fundamental_data(ticker.upper())
    
    if not fundamental_data:
        raise HTTPException(status_code=404, detail=f"Could not build metrics for {ticker}")
    
    all_formulas = FormulaEngine.calculate_all(fundamental_data)
    valuation = FormulaEngine.calculate_valuation_ratios(fundamental_data)
    
    return {
        "ticker": ticker.upper(),
        "core_screeners": all_formulas,
        "valuation_ratios": valuation,
    }


@router.get("/{ticker}/prices")
async def get_prices(
    ticker: str,
    days: int = Query(default=365, le=3650),
):
    """
    Get historical prices for a company.
    """
    from datetime import date, timedelta
    
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    
    prices = await fmp_provider.get_historical_prices(ticker.upper(), from_date, to_date)
    
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "prices": prices,
    }
