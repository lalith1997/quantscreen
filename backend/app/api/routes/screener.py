"""
Screener API routes.

Uses cached daily analysis data when available, falls back to live FMP fetch.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import time

from app.core.database import get_db
from app.models import Company, Screen, DailyAnalysisRun, DailyPick
from app.schemas import (
    ScreenerRequest,
    ScreenerResponse,
    ScreenerResult,
    ScreenCreate,
    ScreenResponse,
)
from app.services.data_providers import fmp_provider
from app.services.formula_engine import FormulaEngine

router = APIRouter(prefix="/screener", tags=["Screener"])


# Pre-built screen configurations
PRESET_SCREENS = {
    "magic_formula": {
        "name": "Magic Formula Top 50",
        "description": "Joel Greenblatt's Magic Formula - highest combined rank of earnings yield and return on capital",
        "filters": [],
        "exclude_sectors": ["Financial Services", "Utilities"],
        "min_market_cap": 50_000_000,
        "sort_by": "magic_formula_rank",
        "sort_order": "asc",
        "limit": 50,
    },
    "deep_value": {
        "name": "Deep Value (Acquirer's Multiple)",
        "description": "Tobias Carlisle's deep value approach - lowest EV/EBIT multiples",
        "filters": [
            {"metric": "acquirers_multiple", "operator": "<", "value": 8},
            {"metric": "f_score", "operator": ">=", "value": 5},
        ],
        "exclude_sectors": ["Financial Services"],
        "min_market_cap": 100_000_000,
        "sort_by": "acquirers_multiple",
        "sort_order": "asc",
        "limit": 50,
    },
    "quality_value": {
        "name": "Quality at Reasonable Price",
        "description": "High F-Score + reasonable valuation",
        "filters": [
            {"metric": "f_score", "operator": ">=", "value": 7},
            {"metric": "pe_ratio", "operator": "<", "value": 20},
            {"metric": "roe", "operator": ">", "value": 15},
        ],
        "min_market_cap": 100_000_000,
        "sort_by": "f_score",
        "sort_order": "desc",
        "limit": 50,
    },
    "safe_stocks": {
        "name": "Financially Safe Stocks",
        "description": "High Z-Score (safe from bankruptcy) + High F-Score",
        "filters": [
            {"metric": "z_score", "operator": ">", "value": 2.99},
            {"metric": "f_score", "operator": ">=", "value": 6},
            {"metric": "m_score_flag", "operator": "==", "value": False},
        ],
        "min_market_cap": 100_000_000,
        "sort_by": "z_score",
        "sort_order": "desc",
        "limit": 50,
    },
    "red_flag_watch": {
        "name": "Manipulation Red Flags",
        "description": "Stocks with concerning M-Score or Accrual Ratio (for research/avoidance)",
        "filters": [
            {"metric": "m_score", "operator": ">", "value": -1.78},
        ],
        "min_market_cap": 500_000_000,
        "sort_by": "m_score",
        "sort_order": "desc",
        "limit": 50,
    },
}


@router.get("/presets")
async def list_preset_screens():
    """
    Get list of pre-built screens.
    """
    return [
        {
            "id": key,
            "name": config["name"],
            "description": config["description"],
        }
        for key, config in PRESET_SCREENS.items()
    ]


@router.get("/presets/{preset_id}")
async def get_preset_screen(preset_id: str):
    """
    Get details of a specific preset screen.
    """
    if preset_id not in PRESET_SCREENS:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    return {"id": preset_id, **PRESET_SCREENS[preset_id]}


@router.post("/presets/{preset_id}/run", response_model=ScreenerResponse)
async def run_preset_screen(
    preset_id: str,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Run a pre-built screen.
    """
    if preset_id not in PRESET_SCREENS:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    config = PRESET_SCREENS[preset_id]
    
    # Build request from preset config
    request = ScreenerRequest(
        filters=[],  # Preset filters applied manually
        sort_by=config.get("sort_by", "market_cap"),
        sort_order=config.get("sort_order", "desc"),
        limit=limit or config.get("limit", 50),
        exclude_sectors=config.get("exclude_sectors", []),
        min_market_cap=config.get("min_market_cap"),
    )
    
    return await run_screen(request, db)


def _get_cached_run(db: Session) -> Optional[DailyAnalysisRun]:
    """Return today's completed DailyAnalysisRun if it exists."""
    return (
        db.query(DailyAnalysisRun)
        .filter(
            DailyAnalysisRun.run_date == date.today(),
            DailyAnalysisRun.status == "completed",
        )
        .first()
    )


def _apply_filters(metrics: dict, filters) -> bool:
    """Apply metric-level filters to a metrics dict. Returns True if it passes."""
    for f in filters:
        value = metrics.get(f.metric)
        if value is None:
            return False
        if f.operator == ">" and not (value > f.value):
            return False
        elif f.operator == "<" and not (value < f.value):
            return False
        elif f.operator == ">=" and not (value >= f.value):
            return False
        elif f.operator == "<=" and not (value <= f.value):
            return False
        elif f.operator == "==" and not (value == f.value):
            return False
    return True


def _run_screen_from_cache(
    db: Session, run: DailyAnalysisRun, request: ScreenerRequest
) -> Optional[ScreenerResponse]:
    """Build screener results from cached DailyPick data. Returns None if cache miss."""
    start_time = time.time()

    # Pull all picks from today's run (across all screens)
    picks = db.query(DailyPick).filter(DailyPick.run_id == run.id).all()
    if not picks:
        return None

    # Build a company lookup for sector / market_cap filtering
    tickers = list({p.ticker for p in picks})
    companies_map = {
        c.ticker: c
        for c in db.query(Company).filter(Company.ticker.in_(tickers)).all()
    }

    results = []
    seen_tickers: set[str] = set()  # dedupe across screens

    for pick in picks:
        if pick.ticker in seen_tickers:
            continue
        company = companies_map.get(pick.ticker)
        if not company:
            continue

        # Apply database-level filters
        if request.exclude_sectors and company.sector in request.exclude_sectors:
            continue
        if request.min_market_cap and (company.market_cap or 0) < request.min_market_cap:
            continue
        if request.max_market_cap and (company.market_cap or 0) > request.max_market_cap:
            continue

        metrics = pick.metrics or {}

        # Apply metric-level filters
        if not _apply_filters(metrics, request.filters):
            continue

        seen_tickers.add(pick.ticker)
        results.append(
            ScreenerResult(
                ticker=company.ticker,
                name=company.name,
                sector=company.sector,
                market_cap=company.market_cap,
                metrics=metrics,
                rank=0,
            )
        )

    # Sort
    sort_key = request.sort_by
    reverse = request.sort_order == "desc"

    def get_sort_value(r):
        val = r.metrics.get(sort_key) or r.market_cap
        return val if val is not None else 0

    results.sort(key=get_sort_value, reverse=reverse)

    for i, result in enumerate(results):
        result.rank = i + 1

    results = results[: request.limit]
    execution_time = (time.time() - start_time) * 1000

    return ScreenerResponse(
        results=results,
        total_count=len(results),
        filters_applied=request.filters,
        execution_time_ms=round(execution_time, 2),
    )


@router.post("/run", response_model=ScreenerResponse)
async def run_screen(
    request: ScreenerRequest,
    db: Session = Depends(get_db),
):
    """
    Run a custom screen with the given filters.

    Uses cached daily analysis data when today's analysis has completed.
    Falls back to live FMP API fetch otherwise.
    """
    # Try cached data first
    cached_run = _get_cached_run(db)
    if cached_run:
        cached_result = _run_screen_from_cache(db, cached_run, request)
        if cached_result:
            return cached_result

    # Fallback: live FMP fetch
    start_time = time.time()

    # Start with base query
    query = db.query(Company).filter(Company.is_active == True)

    # Apply database-level filters
    if request.exclude_sectors:
        query = query.filter(~Company.sector.in_(request.exclude_sectors))
    if request.min_market_cap:
        query = query.filter(Company.market_cap >= request.min_market_cap)
    if request.max_market_cap:
        query = query.filter(Company.market_cap <= request.max_market_cap)

    # Get candidate companies
    companies = query.order_by(Company.market_cap.desc()).limit(200).all()

    results = []

    for company in companies[:50]:  # Limit to 50 for live API calls
        try:
            fundamental_data = await fmp_provider.build_fundamental_data(company.ticker)

            if not fundamental_data:
                continue

            all_formulas = FormulaEngine.calculate_all(fundamental_data)
            valuation = FormulaEngine.calculate_valuation_ratios(fundamental_data)

            # Build metrics dict
            metrics = {}

            # Core screeners
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
            if all_formulas.get("magic_formula"):
                mf = all_formulas["magic_formula"]
                metrics["earnings_yield"] = mf.get("earnings_yield")
                metrics["return_on_capital"] = mf.get("return_on_capital")

            # Valuation ratios
            metrics.update(valuation)

            if not _apply_filters(metrics, request.filters):
                continue

            results.append(ScreenerResult(
                ticker=company.ticker,
                name=company.name,
                sector=company.sector,
                market_cap=company.market_cap,
                metrics=metrics,
                rank=0,
            ))

        except Exception as e:
            print(f"Error processing {company.ticker}: {e}")
            continue

    # Sort results
    sort_key = request.sort_by
    reverse = request.sort_order == "desc"

    def get_sort_value(r):
        val = r.metrics.get(sort_key) or r.market_cap
        return val if val is not None else 0

    results.sort(key=get_sort_value, reverse=reverse)

    # Assign ranks
    for i, result in enumerate(results):
        result.rank = i + 1

    # Apply limit
    results = results[:request.limit]

    execution_time = (time.time() - start_time) * 1000

    return ScreenerResponse(
        results=results,
        total_count=len(results),
        filters_applied=request.filters,
        execution_time_ms=round(execution_time, 2),
    )


@router.get("/saved", response_model=list[ScreenResponse])
async def list_saved_screens(db: Session = Depends(get_db)):
    """
    List user's saved screens.
    """
    screens = db.query(Screen).filter(Screen.is_preset == False).all()
    return screens


@router.post("/saved", response_model=ScreenResponse)
async def save_screen(
    screen: ScreenCreate,
    db: Session = Depends(get_db),
):
    """
    Save a custom screen.
    """
    db_screen = Screen(
        name=screen.name,
        description=screen.description,
        filters=[f.model_dump() for f in screen.filters],
        sort_by=screen.sort_by,
        sort_order=screen.sort_order,
        is_preset=False,
    )
    
    db.add(db_screen)
    db.commit()
    db.refresh(db_screen)
    
    return db_screen


@router.delete("/saved/{screen_id}")
async def delete_screen(screen_id: int, db: Session = Depends(get_db)):
    """
    Delete a saved screen.
    """
    screen = db.query(Screen).filter(Screen.id == screen_id).first()
    
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    if screen.is_preset:
        raise HTTPException(status_code=400, detail="Cannot delete preset screens")
    
    db.delete(screen)
    db.commit()
    
    return {"message": "Screen deleted"}
