"""
Yahoo Finance data provider — replaces FMP for heavy fundamental data fetching.

Uses yfinance (free, no API key) for income statements, balance sheets,
cash flow, quotes, historical prices, and company profiles.
FMP is still used for lightweight calls (news, earnings, market data).
"""

import asyncio
import time
import random
from typing import Optional
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from app.services.formula_engine.formulas import FundamentalData


# ---------------------------------------------------------------------------
# Helper: extract a value from a yfinance DataFrame by trying multiple
# row-label variants (field names vary across tickers and yfinance versions).
# ---------------------------------------------------------------------------

def _safe_extract(
    df: Optional[pd.DataFrame],
    row_labels: list[str],
    col_index: int = 0,
) -> Optional[float]:
    """Try multiple row labels from a yfinance DataFrame, return first found."""
    if df is None or df.empty:
        return None
    for label in row_labels:
        if label in df.index:
            try:
                val = df.iloc[df.index.get_loc(label), col_index]
                if pd.notna(val):
                    return float(val)
            except (IndexError, TypeError, ValueError):
                continue
    return None


def _safe_int(val: Optional[float]) -> Optional[int]:
    """Convert float to int safely."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Retry wrapper for 429 / transient errors
# ---------------------------------------------------------------------------

def _with_retry(func, *args, max_retries: int = 3, base_delay: float = 2.0):
    """Execute a sync function with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            error_str = str(e).lower()
            if ("429" in error_str or "too many requests" in error_str) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"  yfinance rate-limited, sleeping {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            elif attempt < max_retries - 1 and "no data" not in error_str:
                time.sleep(base_delay)
            else:
                raise
    return None


# ---------------------------------------------------------------------------
# YFinanceProvider
# ---------------------------------------------------------------------------

class YFinanceProvider:
    """
    Yahoo Finance data provider for heavy fundamental data fetching.

    All public methods are async (wrapping sync yfinance calls via
    asyncio.to_thread) so they drop into the existing FastAPI/async
    codebase without changes.
    """

    async def close(self):
        """No-op — matches FMPProvider interface for compatibility."""
        pass

    # ========== Core: build_fundamental_data ==========

    async def build_fundamental_data(self, ticker: str) -> Optional[FundamentalData]:
        """
        Fetch all fundamental data and build FundamentalData object.
        Replaces FMP's 5-API-call method with a single yfinance Ticker.
        """
        return await asyncio.to_thread(self._build_fundamental_data_sync, ticker)

    def _build_fundamental_data_sync(self, ticker: str) -> Optional[FundamentalData]:
        """Synchronous implementation."""
        try:
            t = yf.Ticker(ticker)

            income = _with_retry(lambda: t.income_stmt)
            balance = _with_retry(lambda: t.balance_sheet)
            cashflow = _with_retry(lambda: t.cashflow)

            # .info can sometimes raise; wrap in try
            try:
                info = t.info or {}
            except Exception:
                info = {}

            if income is None or income.empty or balance is None or balance.empty:
                return None

            return FundamentalData(
                # --- Income Statement (current period, col 0) ---
                revenue=_safe_extract(income, ["Total Revenue", "Revenue"], 0),
                cost_of_revenue=_safe_extract(income, ["Cost Of Revenue"], 0),
                gross_profit=_safe_extract(income, ["Gross Profit"], 0),
                operating_income=_safe_extract(income, ["Operating Income", "Operating Revenue"], 0),
                ebit=_safe_extract(income, ["EBIT", "Operating Income"], 0),
                ebitda=_safe_extract(income, ["EBITDA", "Normalized EBITDA"], 0),
                net_income=_safe_extract(income, ["Net Income", "Net Income Common Stockholders"], 0),
                eps=_safe_extract(income, ["Basic EPS", "Diluted EPS"], 0),
                sga_expense=_safe_extract(income, [
                    "Selling General And Administration",
                    "Selling General And Administrative",
                ], 0),
                depreciation=_safe_extract(income, [
                    "Reconciled Depreciation",
                    "Depreciation And Amortization In Income Statement",
                    "Depreciation Amortization Depletion",
                ], 0),

                # --- Balance Sheet (current period, col 0) ---
                total_assets=_safe_extract(balance, ["Total Assets"], 0),
                current_assets=_safe_extract(balance, ["Current Assets"], 0),
                total_liabilities=_safe_extract(balance, [
                    "Total Liabilities Net Minority Interest",
                    "Total Liab",
                ], 0),
                current_liabilities=_safe_extract(balance, ["Current Liabilities"], 0),
                total_debt=_safe_extract(balance, ["Total Debt"], 0),
                long_term_debt=_safe_extract(balance, [
                    "Long Term Debt",
                    "Long Term Debt And Capital Lease Obligation",
                ], 0),
                shareholders_equity=_safe_extract(balance, [
                    "Stockholders Equity",
                    "Total Stockholders Equity",
                    "Total Equity Gross Minority Interest",
                ], 0),
                retained_earnings=_safe_extract(balance, ["Retained Earnings"], 0),
                cash_and_equivalents=_safe_extract(balance, [
                    "Cash And Cash Equivalents",
                    "Cash Cash Equivalents And Short Term Investments",
                ], 0),
                net_receivables=_safe_extract(balance, [
                    "Net Receivables",
                    "Receivables",
                    "Accounts Receivable",
                ], 0),
                inventory=_safe_extract(balance, ["Inventory"], 0),
                property_plant_equipment=_safe_extract(balance, [
                    "Net PPE",
                    "Property Plant Equipment Net",
                ], 0),
                intangible_assets=_safe_extract(balance, [
                    "Goodwill And Other Intangible Assets",
                    "Other Intangible Assets",
                ], 0),

                # --- Cash Flow (current period, col 0) ---
                operating_cash_flow=_safe_extract(cashflow, [
                    "Operating Cash Flow",
                    "Cash Flow From Continuing Operating Activities",
                ], 0),
                capital_expenditures=_safe_extract(cashflow, [
                    "Capital Expenditure",
                    "Purchase Of PPE",
                ], 0),
                free_cash_flow=_safe_extract(cashflow, ["Free Cash Flow"], 0),
                dividends_paid=_safe_extract(cashflow, [
                    "Common Stock Dividend Paid",
                    "Cash Dividends Paid",
                ], 0),

                # --- Shares & Price (from .info) ---
                shares_outstanding=_safe_int(info.get("sharesOutstanding")),
                market_cap=info.get("marketCap"),
                stock_price=info.get("currentPrice") or info.get("regularMarketPrice"),

                # --- Prior Period (col 1) ---
                revenue_prior=_safe_extract(income, ["Total Revenue", "Revenue"], 1),
                gross_profit_prior=_safe_extract(income, ["Gross Profit"], 1),
                net_income_prior=_safe_extract(income, ["Net Income", "Net Income Common Stockholders"], 1),
                total_assets_prior=_safe_extract(balance, ["Total Assets"], 1),
                current_assets_prior=_safe_extract(balance, ["Current Assets"], 1),
                current_liabilities_prior=_safe_extract(balance, ["Current Liabilities"], 1),
                long_term_debt_prior=_safe_extract(balance, [
                    "Long Term Debt",
                    "Long Term Debt And Capital Lease Obligation",
                ], 1),
                shares_outstanding_prior=_safe_int(_safe_extract(balance, [
                    "Share Issued",
                    "Ordinary Shares Number",
                ], 1)),
                net_receivables_prior=_safe_extract(balance, [
                    "Net Receivables",
                    "Receivables",
                    "Accounts Receivable",
                ], 1),
                sga_expense_prior=_safe_extract(income, [
                    "Selling General And Administration",
                    "Selling General And Administrative",
                ], 1),
                depreciation_prior=_safe_extract(income, [
                    "Reconciled Depreciation",
                    "Depreciation And Amortization In Income Statement",
                    "Depreciation Amortization Depletion",
                ], 1),
                property_plant_equipment_prior=_safe_extract(balance, [
                    "Net PPE",
                    "Property Plant Equipment Net",
                ], 1),
            )
        except Exception as e:
            print(f"  yfinance error for {ticker}: {e}")
            return None

    # ========== Quotes ==========

    async def get_quote(self, ticker: str) -> Optional[dict]:
        """Get current quote data. Returns dict matching FMP quote format."""
        return await asyncio.to_thread(self._get_quote_sync, ticker)

    def _get_quote_sync(self, ticker: str) -> Optional[dict]:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if not info:
                return None
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if price is None:
                return None
            return {
                "symbol": ticker,
                "price": price,
                "changesPercentage": info.get("regularMarketChangePercent"),
                "change": info.get("regularMarketChange"),
                "marketCap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "volume": info.get("regularMarketVolume"),
                "previousClose": info.get("previousClose"),
                "name": info.get("longName") or info.get("shortName"),
            }
        except Exception as e:
            print(f"  yfinance quote error for {ticker}: {e}")
            return None

    # ========== Historical Prices ==========

    async def get_historical_prices(
        self,
        ticker: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Get historical OHLCV data. Returns list of dicts, newest-first
        (matching FMP convention used throughout the codebase).
        """
        return await asyncio.to_thread(
            self._get_historical_prices_sync, ticker, from_date, to_date
        )

    def _get_historical_prices_sync(
        self,
        ticker: str,
        from_date: Optional[date],
        to_date: Optional[date],
    ) -> list[dict]:
        try:
            t = yf.Ticker(ticker)
            start = from_date.isoformat() if from_date else None
            end = (to_date + timedelta(days=1)).isoformat() if to_date else None

            df = t.history(start=start, end=end, auto_adjust=True)
            if df is None or df.empty:
                return []

            records = []
            for idx, row in df.iterrows():
                records.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })

            # Newest-first to match FMP convention
            records.reverse()
            return records
        except Exception as e:
            print(f"  yfinance historical prices error for {ticker}: {e}")
            return []

    # ========== Financial Statements (raw, for companies.py routes) ==========

    async def get_income_statement(
        self, ticker: str, period: str = "annual", limit: int = 5
    ) -> list[dict]:
        """Get income statements as list of dicts."""
        return await asyncio.to_thread(
            self._get_statement_sync, ticker, "income", period, limit
        )

    async def get_balance_sheet(
        self, ticker: str, period: str = "annual", limit: int = 5
    ) -> list[dict]:
        """Get balance sheets as list of dicts."""
        return await asyncio.to_thread(
            self._get_statement_sync, ticker, "balance", period, limit
        )

    async def get_cash_flow_statement(
        self, ticker: str, period: str = "annual", limit: int = 5
    ) -> list[dict]:
        """Get cash flow statements as list of dicts."""
        return await asyncio.to_thread(
            self._get_statement_sync, ticker, "cashflow", period, limit
        )

    def _get_statement_sync(
        self, ticker: str, statement_type: str, period: str, limit: int
    ) -> list[dict]:
        try:
            t = yf.Ticker(ticker)
            if statement_type == "income":
                df = t.income_stmt if period == "annual" else t.quarterly_income_stmt
            elif statement_type == "balance":
                df = t.balance_sheet if period == "annual" else t.quarterly_balance_sheet
            elif statement_type == "cashflow":
                df = t.cashflow if period == "annual" else t.quarterly_cashflow
            else:
                return []

            if df is None or df.empty:
                return []

            results = []
            for col in df.columns[:limit]:
                record = {"date": col.strftime("%Y-%m-%d")}
                for row_label in df.index:
                    val = df.loc[row_label, col]
                    if pd.notna(val):
                        record[row_label] = float(val)
                results.append(record)
            return results
        except Exception as e:
            print(f"  yfinance {statement_type} error for {ticker}: {e}")
            return []

    # ========== Company Profile ==========

    async def get_company_profile(self, ticker: str) -> Optional[dict]:
        """Get company profile from yfinance .info."""
        return await asyncio.to_thread(self._get_company_profile_sync, ticker)

    def _get_company_profile_sync(self, ticker: str) -> Optional[dict]:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            if not info:
                return None
            return {
                "symbol": ticker,
                "companyName": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "mktCap": info.get("marketCap"),
                "exchange": info.get("exchange"),
                "country": info.get("country"),
                "currency": info.get("currency"),
                "sharesOutstanding": info.get("sharesOutstanding"),
                "description": info.get("longBusinessSummary"),
            }
        except Exception as e:
            print(f"  yfinance profile error for {ticker}: {e}")
            return None


# Singleton instance
yfinance_provider = YFinanceProvider()
