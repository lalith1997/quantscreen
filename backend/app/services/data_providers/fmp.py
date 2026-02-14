"""
Financial Modeling Prep (FMP) API data provider.

Provides fundamental data, company profiles, and financial statements.
API Documentation: https://financialmodelingprep.com/developer/docs/
"""

import httpx
from typing import Optional
from datetime import date
from app.core.config import settings
from app.services.formula_engine import FundamentalData


class FMPProvider:
    """Financial Modeling Prep API client."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.fmp_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _url(self, endpoint: str) -> str:
        """Build URL with API key."""
        separator = "&" if "?" in endpoint else "?"
        return f"{self.BASE_URL}/{endpoint}{separator}apikey={self.api_key}"
    
    async def get_company_profile(self, ticker: str) -> Optional[dict]:
        """
        Get company profile including sector, industry, market cap.
        """
        try:
            response = await self.client.get(self._url(f"profile/{ticker}"))
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
        except Exception as e:
            print(f"Error fetching profile for {ticker}: {e}")
            return None
    
    async def get_income_statement(self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        """
        Get income statements.
        
        Args:
            ticker: Stock symbol
            period: "annual" or "quarter"
            limit: Number of periods to fetch
        """
        try:
            response = await self.client.get(
                self._url(f"income-statement/{ticker}?period={period}&limit={limit}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching income statement for {ticker}: {e}")
            return []
    
    async def get_balance_sheet(self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        """Get balance sheet statements."""
        try:
            response = await self.client.get(
                self._url(f"balance-sheet-statement/{ticker}?period={period}&limit={limit}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching balance sheet for {ticker}: {e}")
            return []
    
    async def get_cash_flow_statement(self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        """Get cash flow statements."""
        try:
            response = await self.client.get(
                self._url(f"cash-flow-statement/{ticker}?period={period}&limit={limit}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching cash flow for {ticker}: {e}")
            return []
    
    async def get_key_metrics(self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        """Get pre-calculated key metrics."""
        try:
            response = await self.client.get(
                self._url(f"key-metrics/{ticker}?period={period}&limit={limit}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching key metrics for {ticker}: {e}")
            return []
    
    async def get_financial_ratios(self, ticker: str, period: str = "annual", limit: int = 5) -> list[dict]:
        """Get pre-calculated financial ratios."""
        try:
            response = await self.client.get(
                self._url(f"ratios/{ticker}?period={period}&limit={limit}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching ratios for {ticker}: {e}")
            return []
    
    async def get_quote(self, ticker: str) -> Optional[dict]:
        """Get current stock quote."""
        try:
            response = await self.client.get(self._url(f"quote/{ticker}"))
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            return None
        except Exception as e:
            print(f"Error fetching quote for {ticker}: {e}")
            return None
    
    async def get_historical_prices(
        self, 
        ticker: str, 
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> list[dict]:
        """Get historical daily prices."""
        try:
            url = f"historical-price-full/{ticker}?"
            if from_date:
                url += f"from={from_date.isoformat()}&"
            if to_date:
                url += f"to={to_date.isoformat()}&"
            
            response = await self.client.get(self._url(url))
            response.raise_for_status()
            data = response.json()
            return data.get("historical", [])
        except Exception as e:
            print(f"Error fetching historical prices for {ticker}: {e}")
            return []
    
    async def get_stock_list(self) -> list[dict]:
        """Get list of all available stocks."""
        try:
            response = await self.client.get(self._url("stock/list"))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            return []
    
    async def get_sp500_constituents(self) -> list[dict]:
        """Get S&P 500 constituent list."""
        try:
            response = await self.client.get(self._url("sp500_constituent"))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching S&P 500 list: {e}")
            return []
    
    async def build_fundamental_data(self, ticker: str) -> Optional[FundamentalData]:
        """
        Fetch all data and build FundamentalData object for formula calculations.
        """
        # Fetch all required data
        profile = await self.get_company_profile(ticker)
        income = await self.get_income_statement(ticker, "annual", 2)
        balance = await self.get_balance_sheet(ticker, "annual", 2)
        cashflow = await self.get_cash_flow_statement(ticker, "annual", 2)
        quote = await self.get_quote(ticker)
        
        if not income or not balance:
            return None
        
        # Current period (most recent)
        inc = income[0] if income else {}
        bal = balance[0] if balance else {}
        cf = cashflow[0] if cashflow else {}
        
        # Prior period
        inc_prior = income[1] if len(income) > 1 else {}
        bal_prior = balance[1] if len(balance) > 1 else {}
        
        return FundamentalData(
            # Income Statement - Current
            revenue=inc.get("revenue"),
            cost_of_revenue=inc.get("costOfRevenue"),
            gross_profit=inc.get("grossProfit"),
            operating_income=inc.get("operatingIncome"),
            ebit=inc.get("operatingIncome"),  # FMP uses operatingIncome as EBIT
            ebitda=inc.get("ebitda"),
            net_income=inc.get("netIncome"),
            eps=inc.get("eps"),
            sga_expense=inc.get("sellingGeneralAndAdministrativeExpenses"),
            depreciation=inc.get("depreciationAndAmortization"),
            
            # Balance Sheet - Current
            total_assets=bal.get("totalAssets"),
            current_assets=bal.get("totalCurrentAssets"),
            total_liabilities=bal.get("totalLiabilities"),
            current_liabilities=bal.get("totalCurrentLiabilities"),
            total_debt=bal.get("totalDebt"),
            long_term_debt=bal.get("longTermDebt"),
            shareholders_equity=bal.get("totalStockholdersEquity"),
            retained_earnings=bal.get("retainedEarnings"),
            cash_and_equivalents=bal.get("cashAndCashEquivalents"),
            net_receivables=bal.get("netReceivables"),
            inventory=bal.get("inventory"),
            property_plant_equipment=bal.get("propertyPlantEquipmentNet"),
            intangible_assets=bal.get("intangibleAssets"),
            
            # Cash Flow
            operating_cash_flow=cf.get("operatingCashFlow"),
            capital_expenditures=cf.get("capitalExpenditure"),
            free_cash_flow=cf.get("freeCashFlow"),
            dividends_paid=cf.get("dividendsPaid"),
            
            # Shares & Price
            shares_outstanding=bal.get("commonStock") or (profile.get("sharesOutstanding") if profile else None),
            market_cap=profile.get("mktCap") if profile else None,
            stock_price=quote.get("price") if quote else None,
            
            # Prior Period
            revenue_prior=inc_prior.get("revenue"),
            gross_profit_prior=inc_prior.get("grossProfit"),
            net_income_prior=inc_prior.get("netIncome"),
            total_assets_prior=bal_prior.get("totalAssets"),
            current_assets_prior=bal_prior.get("totalCurrentAssets"),
            current_liabilities_prior=bal_prior.get("totalCurrentLiabilities"),
            long_term_debt_prior=bal_prior.get("longTermDebt"),
            shares_outstanding_prior=bal_prior.get("commonStock"),
            net_receivables_prior=bal_prior.get("netReceivables"),
            sga_expense_prior=inc_prior.get("sellingGeneralAndAdministrativeExpenses"),
            depreciation_prior=inc_prior.get("depreciationAndAmortization"),
            property_plant_equipment_prior=bal_prior.get("propertyPlantEquipmentNet"),
        )


# Singleton instance
fmp_provider = FMPProvider()
