"""
Daily analysis engine — the core orchestrator.
Runs at 6 AM ET via APScheduler. Fetches data, calculates metrics,
applies filters, generates strategies, and fetches news.
"""

import asyncio
import time
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Company, DailyAnalysisRun, DailyPick
from app.services.data_providers import YFinanceProvider
from app.services.formula_engine import FormulaEngine
from app.api.routes.screener import PRESET_SCREENS


async def run_daily_analysis(force: bool = False):
    """
    Main daily analysis orchestrator. Called by APScheduler at 6 AM ET.
    Can also be triggered manually via POST /api/daily-brief/trigger.
    Use force=True to re-run even if already completed today.
    """
    db = SessionLocal()
    try:
        today = date.today()

        # Check if already completed today (skip check if forced)
        if not force:
            existing = (
                db.query(DailyAnalysisRun)
                .filter(
                    DailyAnalysisRun.run_date == today,
                    DailyAnalysisRun.status == "completed",
                )
                .first()
            )
            if existing:
                print(f"Daily analysis already completed for {today}")
                return

        # Delete any previous runs for today (allow re-runs)
        old_runs = (
            db.query(DailyAnalysisRun)
            .filter(DailyAnalysisRun.run_date == today)
            .all()
        )
        if old_runs:
            old_run_ids = [r.id for r in old_runs]
            # Delete picks first (child records)
            db.query(DailyPick).filter(
                DailyPick.run_id.in_(old_run_ids)
            ).delete(synchronize_session=False)
            # Then delete the runs
            db.query(DailyAnalysisRun).filter(
                DailyAnalysisRun.run_date == today
            ).delete(synchronize_session=False)
        db.commit()

        # Create new run record
        run = DailyAnalysisRun(
            run_date=today,
            started_at=datetime.utcnow(),
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        start = time.time()
        print(f"Starting daily analysis for {today}...")

        # Step 1: Market risk assessment (fast, ~5 seconds)
        try:
            from app.services.market_risk import compute_market_risk
            await compute_market_risk(db)
            print("  Market risk computed")
        except Exception as e:
            print(f"  Warning: Market risk computation failed: {e}")

        # Step 2: Sync S&P 500 universe (occasional)
        try:
            from app.core.seed import sync_sp500_universe
            stats = await sync_sp500_universe(db)
            if stats["added"] > 0:
                print(f"  Universe sync: added {stats['added']} new companies")
        except Exception as e:
            print(f"  Warning: Universe sync failed: {e}")

        # Step 3: Fetch fundamentals and calculate metrics for all active stocks
        companies = db.query(Company).filter(Company.is_active == True).all()
        print(f"  Analyzing {len(companies)} companies...")

        all_results = await _fetch_and_calculate_all(companies)
        print(f"  Calculated metrics for {len(all_results)} companies")

        # Step 4: Apply preset filters and generate daily picks
        picks_count = _generate_daily_picks(db, run.id, all_results)
        print(f"  Generated {picks_count} picks across all screens")

        # Step 5: Generate strategies for picked stocks
        try:
            from app.services.strategy_engine import generate_strategies_for_picks
            await generate_strategies_for_picks(db, run.id)
            print("  Strategies generated")
        except Exception as e:
            print(f"  Warning: Strategy generation failed: {e}")

        # Step 6: Fetch news for picked stocks
        try:
            from app.services.news_service import fetch_news_for_picks, fetch_market_news
            await fetch_news_for_picks(db, run.id)
            await fetch_market_news(db)
            print("  News fetched")
        except Exception as e:
            print(f"  Warning: News fetching failed: {e}")

        # Step 7: Tag picks with earnings calendar data
        try:
            from app.services.earnings_service import fetch_and_tag_earnings
            await fetch_and_tag_earnings(db, run.id)
            print("  Earnings tagged")
        except Exception as e:
            print(f"  Warning: Earnings tagging failed: {e}")

        # Step 8: Portfolio health check (only if user has holdings)
        try:
            from app.models import PortfolioHolding
            has_holdings = db.query(PortfolioHolding).filter(
                PortfolioHolding.is_active == True
            ).first()
            if has_holdings:
                from app.services.portfolio_service import run_portfolio_analysis
                await run_portfolio_analysis(db)
                print("  Portfolio analysis completed")
        except Exception as e:
            print(f"  Warning: Portfolio analysis failed: {e}")

        # Update run metadata
        elapsed = time.time() - start
        run.completed_at = datetime.utcnow()
        run.stocks_analyzed = len(all_results)
        run.stocks_passed = picks_count
        run.status = "completed"
        run.execution_time_seconds = round(elapsed, 2)
        db.commit()

        print(
            f"Daily analysis completed: {len(all_results)} stocks analyzed, "
            f"{picks_count} picks, {elapsed:.1f}s elapsed"
        )

    except Exception as e:
        print(f"Daily analysis failed: {e}")
        try:
            run.status = "failed"
            run.error_message = str(e)[:1000]
            run.completed_at = datetime.utcnow()
            db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


async def _fetch_and_calculate_all(
    companies: list[Company],
    concurrency: int = 4,
) -> dict[str, dict]:
    """
    Fetch fundamental data and calculate all metrics for every company.
    Uses yfinance (free, no API key) instead of FMP to avoid rate limits.
    Processes in batches with delays to respect Yahoo Finance rate limits.
    """
    results = {}
    batch_size = 10
    yf_provider = YFinanceProvider()

    async def process_one(company: Company, semaphore: asyncio.Semaphore):
        async with semaphore:
            try:
                # Skip fundamental formulas for ETFs (no income statements)
                if company.is_etf:
                    quote = await yf_provider.get_quote(company.ticker)
                    if quote:
                        results[company.ticker] = {
                            "company": company,
                            "metrics": {
                                "stock_price": quote.get("price"),
                                "market_cap": quote.get("marketCap"),
                                "pe_ratio": quote.get("pe"),
                                "volume": quote.get("volume"),
                            },
                            "is_etf": True,
                        }
                    return

                data = await yf_provider.build_fundamental_data(company.ticker)

                if data:
                    formulas = FormulaEngine.calculate_all(data)
                    valuation = FormulaEngine.calculate_valuation_ratios(data)
                    metrics = _flatten_metrics(formulas, valuation)
                    results[company.ticker] = {
                        "company": company,
                        "metrics": metrics,
                        "is_etf": False,
                    }
            except Exception as e:
                print(f"  Error processing {company.ticker}: {e}")

    # Process in batches to respect Yahoo Finance rate limits
    semaphore = asyncio.Semaphore(concurrency)
    for i in range(0, len(companies), batch_size):
        batch = companies[i : i + batch_size]
        tasks = [process_one(c, semaphore) for c in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        # Pause between batches to avoid 429s from Yahoo Finance
        if i + batch_size < len(companies):
            await asyncio.sleep(2.0)
        processed = min(i + batch_size, len(companies))
        if processed % 50 == 0 or processed == len(companies):
            print(f"  Processed {processed}/{len(companies)} companies...")

    await yf_provider.close()
    return results


def _flatten_metrics(formulas: dict, valuation: dict) -> dict:
    """
    Flatten nested formula results into a flat metrics dict.
    Matches the pattern from screener.py for consistency.
    """
    metrics = {}

    # Core screeners
    if formulas.get("piotroski"):
        metrics["f_score"] = formulas["piotroski"]["f_score"]
    if formulas.get("acquirers_multiple"):
        metrics["acquirers_multiple"] = formulas["acquirers_multiple"]
    if formulas.get("altman_z"):
        metrics["z_score"] = formulas["altman_z"]["z_score"]
    if formulas.get("beneish_m"):
        metrics["m_score"] = formulas["beneish_m"]["m_score"]
        metrics["m_score_flag"] = formulas["beneish_m"]["is_red_flag"]
    if formulas.get("sloan_accrual"):
        metrics["accrual_ratio"] = formulas["sloan_accrual"]["accrual_ratio_pct"]
    if formulas.get("magic_formula"):
        mf = formulas["magic_formula"]
        metrics["earnings_yield"] = mf.get("earnings_yield")
        metrics["return_on_capital"] = mf.get("return_on_capital")

    # Valuation ratios
    metrics.update(valuation)

    return metrics


def _generate_daily_picks(
    db: Session, run_id: int, all_results: dict[str, dict]
) -> int:
    """
    Apply each preset screen to calculated results and store picks.
    Returns total number of picks generated.
    """
    # Clear any existing picks for this run (allows re-runs)
    db.query(DailyPick).filter(DailyPick.run_id == run_id).delete(
        synchronize_session=False
    )

    total_picks = 0

    for screen_name, config in PRESET_SCREENS.items():
        # Skip the red flag screen — it's for avoidance, not picks
        if screen_name == "red_flag_watch":
            continue

        candidates = []

        for ticker, result in all_results.items():
            # Skip ETFs for fundamental-based screens
            if result.get("is_etf"):
                continue

            company = result["company"]
            metrics = result["metrics"]

            # Apply sector exclusions
            if company.sector in config.get("exclude_sectors", []):
                continue

            # Apply market cap minimum
            min_cap = config.get("min_market_cap")
            if min_cap and (company.market_cap or 0) < min_cap:
                continue

            # Apply metric-level filters
            passes = True
            for f in config.get("filters", []):
                val = metrics.get(f["metric"])
                if val is None:
                    passes = False
                    break

                op = f["operator"]
                target = f["value"]
                if op == ">" and not (val > target):
                    passes = False
                elif op == "<" and not (val < target):
                    passes = False
                elif op == ">=" and not (val >= target):
                    passes = False
                elif op == "<=" and not (val <= target):
                    passes = False
                elif op == "==" and not (val == target):
                    passes = False

                if not passes:
                    break

            if passes:
                candidates.append((ticker, metrics, company))

        # Sort by configured sort key
        sort_key = config.get("sort_by", "market_cap")
        reverse = config.get("sort_order", "desc") == "desc"

        def sort_fn(item):
            val = item[1].get(sort_key)
            if val is not None:
                return val
            return item[2].market_cap or 0

        candidates.sort(key=sort_fn, reverse=reverse)

        # Store top N picks
        limit = config.get("limit", 50)
        for rank, (ticker, metrics, company) in enumerate(
            candidates[:limit], 1
        ):
            # Serialize metrics — convert non-serializable values
            safe_metrics = {}
            for k, v in metrics.items():
                if isinstance(v, (int, float, bool, str, type(None))):
                    safe_metrics[k] = v

            pick = DailyPick(
                run_id=run_id,
                ticker=ticker,
                screen_name=screen_name,
                metrics=safe_metrics,
                rank=rank,
                rationale=_build_rationale(screen_name, metrics, company),
            )
            db.add(pick)
            total_picks += 1

    db.commit()
    return total_picks


def _build_rationale(screen_name: str, metrics: dict, company: Company) -> str:
    """Generate a plain English explanation a college student could understand."""
    from app.services.rationale_helpers import explain_metric

    parts = []

    if screen_name == "magic_formula":
        ey = metrics.get("earnings_yield")
        roc = metrics.get("return_on_capital")
        parts.append(
            f"{company.name} looks like a great deal — it's both cheap "
            f"and highly profitable."
        )
        if ey is not None:
            parts.append(explain_metric("earnings_yield", ey))
        if roc is not None:
            parts.append(explain_metric("return_on_capital", roc))

    elif screen_name == "deep_value":
        am = metrics.get("acquirers_multiple")
        fs = metrics.get("f_score")
        parts.append(
            f"{company.name} is trading at a big discount — you're getting "
            f"a lot of business for your money."
        )
        if am is not None:
            parts.append(explain_metric("acquirers_multiple", am))
        if fs is not None:
            parts.append(explain_metric("f_score", fs))

    elif screen_name == "quality_value":
        fs = metrics.get("f_score")
        pe = metrics.get("pe_ratio")
        roe = metrics.get("roe")
        parts.append(
            f"{company.name} is a strong company at a fair price — "
            f"you're not overpaying for quality."
        )
        if fs is not None:
            parts.append(explain_metric("f_score", fs))
        if pe is not None:
            parts.append(explain_metric("pe_ratio", pe))
        if roe is not None:
            parts.append(explain_metric("roe", roe))

    elif screen_name == "safe_stocks":
        zs = metrics.get("z_score")
        fs = metrics.get("f_score")
        parts.append(
            f"{company.name} is financially rock-solid — very low risk "
            f"of going bankrupt, and the books look clean."
        )
        if zs is not None:
            parts.append(explain_metric("z_score", zs))
        if fs is not None:
            parts.append(explain_metric("f_score", fs))

    else:
        parts.append(f"{company.name} passed the {screen_name} screen.")

    return " ".join(parts)
