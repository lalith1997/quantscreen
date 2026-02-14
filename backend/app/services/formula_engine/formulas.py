"""
Formula Engine - Core financial calculations for QuantScreen.

Implements:
1. Magic Formula (Greenblatt)
2. Acquirer's Multiple (Carlisle)
3. Piotroski F-Score
4. Altman Z-Score
5. Beneish M-Score
6. Sloan Accrual Ratio
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import numpy as np


@dataclass
class FundamentalData:
    """Container for fundamental data needed by formulas."""
    # Income Statement
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    sga_expense: Optional[float] = None
    depreciation: Optional[float] = None
    
    # Balance Sheet - Current Period
    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    shareholders_equity: Optional[float] = None
    retained_earnings: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    net_receivables: Optional[float] = None
    inventory: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    intangible_assets: Optional[float] = None
    
    # Cash Flow
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividends_paid: Optional[float] = None
    
    # Shares & Price
    shares_outstanding: Optional[int] = None
    market_cap: Optional[float] = None
    stock_price: Optional[float] = None
    
    # Prior Period (for YoY comparisons)
    revenue_prior: Optional[float] = None
    gross_profit_prior: Optional[float] = None
    net_income_prior: Optional[float] = None
    total_assets_prior: Optional[float] = None
    current_assets_prior: Optional[float] = None
    current_liabilities_prior: Optional[float] = None
    long_term_debt_prior: Optional[float] = None
    shares_outstanding_prior: Optional[int] = None
    net_receivables_prior: Optional[float] = None
    sga_expense_prior: Optional[float] = None
    depreciation_prior: Optional[float] = None
    property_plant_equipment_prior: Optional[float] = None
    cash_and_equivalents_prior: Optional[float] = None


def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safely divide two numbers, returning None if impossible."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


class MagicFormula:
    """
    Joel Greenblatt's Magic Formula.
    
    Ranks stocks by combining:
    1. Earnings Yield (EBIT / Enterprise Value) - higher is better
    2. Return on Capital (EBIT / (Net Working Capital + Net Fixed Assets)) - higher is better
    
    Lower combined rank = better investment
    """
    
    @staticmethod
    def calculate_earnings_yield(data: FundamentalData) -> Optional[float]:
        """
        Earnings Yield = EBIT / Enterprise Value
        
        Enterprise Value = Market Cap + Total Debt - Cash
        """
        if data.ebit is None or data.market_cap is None:
            return None
        
        total_debt = data.total_debt or 0
        cash = data.cash_and_equivalents or 0
        
        enterprise_value = data.market_cap + total_debt - cash
        
        if enterprise_value <= 0:
            return None
            
        return data.ebit / enterprise_value
    
    @staticmethod
    def calculate_return_on_capital(data: FundamentalData) -> Optional[float]:
        """
        Return on Capital = EBIT / (Net Working Capital + Net Fixed Assets)
        
        Net Working Capital = Current Assets - Current Liabilities
        Net Fixed Assets = Total Assets - Current Assets - Intangible Assets
        """
        if data.ebit is None:
            return None
        
        current_assets = data.current_assets or 0
        current_liabilities = data.current_liabilities or 0
        total_assets = data.total_assets or 0
        intangibles = (data.intangible_assets or 0) + (data.goodwill if hasattr(data, 'goodwill') and data.goodwill else 0)
        
        net_working_capital = current_assets - current_liabilities
        net_fixed_assets = total_assets - current_assets - intangibles
        
        invested_capital = net_working_capital + net_fixed_assets
        
        if invested_capital <= 0:
            return None
            
        return data.ebit / invested_capital
    
    @staticmethod
    def calculate(data: FundamentalData) -> dict:
        """Calculate both Magic Formula components."""
        return {
            "earnings_yield": MagicFormula.calculate_earnings_yield(data),
            "return_on_capital": MagicFormula.calculate_return_on_capital(data),
        }


class AcquirersMultiple:
    """
    Tobias Carlisle's Acquirer's Multiple.
    
    Acquirer's Multiple = Enterprise Value / Operating Earnings (EBIT)
    
    Lower multiple = more undervalued (deep value)
    Typically: < 5x is deep value, 5-10x is value, > 15x is expensive
    """
    
    @staticmethod
    def calculate(data: FundamentalData) -> Optional[float]:
        """Calculate Acquirer's Multiple."""
        if data.ebit is None or data.market_cap is None:
            return None
        
        if data.ebit <= 0:
            return None  # Negative earnings = not applicable
        
        total_debt = data.total_debt or 0
        cash = data.cash_and_equivalents or 0
        
        enterprise_value = data.market_cap + total_debt - cash
        
        if enterprise_value <= 0:
            return None
        
        return enterprise_value / data.ebit


class PiotroskiFScore:
    """
    Piotroski F-Score (0-9 scale).
    
    Measures financial strength across 9 criteria:
    - Profitability (4 points)
    - Leverage & Liquidity (3 points)
    - Operating Efficiency (2 points)
    
    Score 8-9: Strong, 5-7: Moderate, 0-4: Weak
    """
    
    @staticmethod
    def calculate(data: FundamentalData) -> dict:
        """Calculate F-Score and breakdown."""
        scores = {}
        
        # === PROFITABILITY (4 points) ===
        
        # 1. ROA > 0 (Net Income / Total Assets > 0)
        roa = safe_divide(data.net_income, data.total_assets)
        scores["roa_positive"] = 1 if roa is not None and roa > 0 else 0
        
        # 2. Operating Cash Flow > 0
        scores["cfo_positive"] = 1 if data.operating_cash_flow is not None and data.operating_cash_flow > 0 else 0
        
        # 3. ROA Improving (ROA current > ROA prior)
        roa_prior = safe_divide(data.net_income_prior, data.total_assets_prior)
        if roa is not None and roa_prior is not None:
            scores["roa_improving"] = 1 if roa > roa_prior else 0
        else:
            scores["roa_improving"] = 0
        
        # 4. Accruals (Quality): CFO > Net Income
        if data.operating_cash_flow is not None and data.net_income is not None:
            scores["accruals_quality"] = 1 if data.operating_cash_flow > data.net_income else 0
        else:
            scores["accruals_quality"] = 0
        
        # === LEVERAGE & LIQUIDITY (3 points) ===
        
        # 5. Leverage Decreasing (LT Debt / Assets decreased)
        leverage = safe_divide(data.long_term_debt, data.total_assets)
        leverage_prior = safe_divide(data.long_term_debt_prior, data.total_assets_prior)
        if leverage is not None and leverage_prior is not None:
            scores["leverage_decreasing"] = 1 if leverage < leverage_prior else 0
        else:
            scores["leverage_decreasing"] = 0
        
        # 6. Liquidity Improving (Current Ratio increased)
        current_ratio = safe_divide(data.current_assets, data.current_liabilities)
        current_ratio_prior = safe_divide(data.current_assets_prior, data.current_liabilities_prior)
        if current_ratio is not None and current_ratio_prior is not None:
            scores["liquidity_improving"] = 1 if current_ratio > current_ratio_prior else 0
        else:
            scores["liquidity_improving"] = 0
        
        # 7. No Dilution (Shares Outstanding <= Prior)
        if data.shares_outstanding is not None and data.shares_outstanding_prior is not None:
            scores["no_dilution"] = 1 if data.shares_outstanding <= data.shares_outstanding_prior else 0
        else:
            scores["no_dilution"] = 0
        
        # === OPERATING EFFICIENCY (2 points) ===
        
        # 8. Gross Margin Improving
        gross_margin = safe_divide(data.gross_profit, data.revenue)
        gross_margin_prior = safe_divide(data.gross_profit_prior, data.revenue_prior)
        if gross_margin is not None and gross_margin_prior is not None:
            scores["gross_margin_improving"] = 1 if gross_margin > gross_margin_prior else 0
        else:
            scores["gross_margin_improving"] = 0
        
        # 9. Asset Turnover Improving (Revenue / Assets increased)
        asset_turnover = safe_divide(data.revenue, data.total_assets)
        asset_turnover_prior = safe_divide(data.revenue_prior, data.total_assets_prior)
        if asset_turnover is not None and asset_turnover_prior is not None:
            scores["asset_turnover_improving"] = 1 if asset_turnover > asset_turnover_prior else 0
        else:
            scores["asset_turnover_improving"] = 0
        
        # Calculate total
        total = sum(scores.values())
        
        return {
            "f_score": total,
            "breakdown": scores,
            "interpretation": "Strong" if total >= 8 else "Moderate" if total >= 5 else "Weak"
        }


class AltmanZScore:
    """
    Altman Z-Score - Bankruptcy risk predictor.
    
    Z = 1.2×A + 1.4×B + 3.3×C + 0.6×D + 1.0×E
    
    Where:
    A = Working Capital / Total Assets
    B = Retained Earnings / Total Assets
    C = EBIT / Total Assets
    D = Market Value of Equity / Total Liabilities
    E = Sales / Total Assets
    
    Interpretation:
    Z > 2.99: Safe zone
    1.81 < Z < 2.99: Grey zone
    Z < 1.81: Distress zone
    """
    
    @staticmethod
    def calculate(data: FundamentalData) -> Optional[dict]:
        """Calculate Z-Score and components."""
        if data.total_assets is None or data.total_assets <= 0:
            return None
        
        # A: Working Capital / Total Assets
        working_capital = (data.current_assets or 0) - (data.current_liabilities or 0)
        a = working_capital / data.total_assets
        
        # B: Retained Earnings / Total Assets
        b = safe_divide(data.retained_earnings, data.total_assets) or 0
        
        # C: EBIT / Total Assets
        c = safe_divide(data.ebit, data.total_assets) or 0
        
        # D: Market Value of Equity / Total Liabilities
        if data.total_liabilities is None or data.total_liabilities <= 0:
            d = 0
        else:
            d = safe_divide(data.market_cap, data.total_liabilities) or 0
        
        # E: Sales / Total Assets
        e = safe_divide(data.revenue, data.total_assets) or 0
        
        # Calculate Z-Score
        z_score = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
        
        # Interpretation
        if z_score > 2.99:
            interpretation = "Safe"
        elif z_score > 1.81:
            interpretation = "Grey Zone"
        else:
            interpretation = "Distress"
        
        return {
            "z_score": round(z_score, 2),
            "components": {"A": a, "B": b, "C": c, "D": d, "E": e},
            "interpretation": interpretation
        }


class BeneishMScore:
    """
    Beneish M-Score - Earnings manipulation detector.
    
    M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI 
        + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI
    
    Interpretation:
    M > -1.78: High probability of manipulation (RED FLAG)
    M < -1.78: Low probability (likely clean)
    """
    
    @staticmethod
    def calculate(data: FundamentalData) -> Optional[dict]:
        """Calculate M-Score and components."""
        # Need prior period data for most components
        if data.revenue is None or data.revenue_prior is None:
            return None
        if data.revenue <= 0 or data.revenue_prior <= 0:
            return None
        
        components = {}
        
        # DSRI: Days Sales Receivable Index
        receivables_to_sales = safe_divide(data.net_receivables, data.revenue)
        receivables_to_sales_prior = safe_divide(data.net_receivables_prior, data.revenue_prior)
        dsri = safe_divide(receivables_to_sales, receivables_to_sales_prior) or 1.0
        components["DSRI"] = dsri
        
        # GMI: Gross Margin Index
        gross_margin = safe_divide(data.gross_profit, data.revenue)
        gross_margin_prior = safe_divide(data.gross_profit_prior, data.revenue_prior)
        gmi = safe_divide(gross_margin_prior, gross_margin) or 1.0
        components["GMI"] = gmi
        
        # AQI: Asset Quality Index
        # AQI = [1 - (CA + PPE) / TA] current / [1 - (CA + PPE) / TA] prior
        ca = data.current_assets or 0
        ppe = data.property_plant_equipment or 0
        ta = data.total_assets or 1
        ca_prior = data.current_assets_prior or 0
        ppe_prior = data.property_plant_equipment_prior or 0
        ta_prior = data.total_assets_prior or 1
        
        aq_current = 1 - (ca + ppe) / ta if ta > 0 else 0
        aq_prior = 1 - (ca_prior + ppe_prior) / ta_prior if ta_prior > 0 else 0
        aqi = safe_divide(aq_current, aq_prior) or 1.0
        components["AQI"] = aqi
        
        # SGI: Sales Growth Index
        sgi = data.revenue / data.revenue_prior
        components["SGI"] = sgi
        
        # DEPI: Depreciation Index
        depr_rate = safe_divide(data.depreciation, data.depreciation + ppe) if ppe else None
        depr_rate_prior = safe_divide(data.depreciation_prior, data.depreciation_prior + ppe_prior) if ppe_prior else None
        depi = safe_divide(depr_rate_prior, depr_rate) or 1.0
        components["DEPI"] = depi
        
        # SGAI: SG&A Index
        sga_to_sales = safe_divide(data.sga_expense, data.revenue)
        sga_to_sales_prior = safe_divide(data.sga_expense_prior, data.revenue_prior)
        sgai = safe_divide(sga_to_sales, sga_to_sales_prior) or 1.0
        components["SGAI"] = sgai
        
        # TATA: Total Accruals to Total Assets
        net_income = data.net_income or 0
        cfo = data.operating_cash_flow or 0
        tata = (net_income - cfo) / ta if ta > 0 else 0
        components["TATA"] = tata
        
        # LVGI: Leverage Index
        leverage = safe_divide((data.long_term_debt or 0) + (data.current_liabilities or 0), ta)
        leverage_prior = safe_divide((data.long_term_debt_prior or 0) + (data.current_liabilities_prior or 0), ta_prior)
        lvgi = safe_divide(leverage, leverage_prior) or 1.0
        components["LVGI"] = lvgi
        
        # Calculate M-Score
        m_score = (
            -4.84
            + 0.92 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )
        
        return {
            "m_score": round(m_score, 2),
            "components": components,
            "interpretation": "High manipulation risk" if m_score > -1.78 else "Low manipulation risk",
            "is_red_flag": m_score > -1.78
        }


class SloanAccrualRatio:
    """
    Sloan Accrual Ratio - Earnings quality measure.
    
    Accrual Ratio = (Net Income - Operating Cash Flow) / Average Total Assets
    
    Interpretation:
    < -10%: High quality earnings (cash > income)
    -10% to +10%: Normal
    > +10%: Low quality earnings (RED FLAG)
    
    Lower (more negative) = better quality
    """
    
    @staticmethod
    def calculate(data: FundamentalData) -> Optional[dict]:
        """Calculate Sloan Accrual Ratio."""
        if data.net_income is None or data.operating_cash_flow is None:
            return None
        
        # Average total assets
        ta_current = data.total_assets or 0
        ta_prior = data.total_assets_prior or ta_current
        avg_total_assets = (ta_current + ta_prior) / 2
        
        if avg_total_assets <= 0:
            return None
        
        accruals = data.net_income - data.operating_cash_flow
        accrual_ratio = accruals / avg_total_assets
        
        # Interpretation
        if accrual_ratio < -0.10:
            quality = "High"
            interpretation = "Cash earnings exceed reported income"
        elif accrual_ratio > 0.10:
            quality = "Low"
            interpretation = "Reported income exceeds cash earnings (RED FLAG)"
        else:
            quality = "Normal"
            interpretation = "Earnings quality is normal"
        
        return {
            "accrual_ratio": round(accrual_ratio, 4),
            "accrual_ratio_pct": round(accrual_ratio * 100, 2),
            "quality": quality,
            "interpretation": interpretation,
            "is_red_flag": accrual_ratio > 0.10
        }


class FormulaEngine:
    """
    Main formula engine that calculates all metrics.
    """
    
    @staticmethod
    def calculate_all(data: FundamentalData) -> dict:
        """Calculate all formulas for a stock."""
        results = {}
        
        # Magic Formula
        mf = MagicFormula.calculate(data)
        results["magic_formula"] = mf
        
        # Acquirer's Multiple
        results["acquirers_multiple"] = AcquirersMultiple.calculate(data)
        
        # Piotroski F-Score
        results["piotroski"] = PiotroskiFScore.calculate(data)
        
        # Altman Z-Score
        results["altman_z"] = AltmanZScore.calculate(data)
        
        # Beneish M-Score
        results["beneish_m"] = BeneishMScore.calculate(data)
        
        # Sloan Accrual Ratio
        results["sloan_accrual"] = SloanAccrualRatio.calculate(data)
        
        return results
    
    @staticmethod
    def calculate_valuation_ratios(data: FundamentalData) -> dict:
        """Calculate common valuation ratios."""
        ratios = {}
        
        # P/E Ratio
        if data.stock_price and data.eps:
            ratios["pe_ratio"] = round(data.stock_price / data.eps, 2) if data.eps > 0 else None
        
        # P/B Ratio
        if data.market_cap and data.shareholders_equity:
            ratios["pb_ratio"] = round(data.market_cap / data.shareholders_equity, 2) if data.shareholders_equity > 0 else None
        
        # P/S Ratio
        if data.market_cap and data.revenue:
            ratios["ps_ratio"] = round(data.market_cap / data.revenue, 2) if data.revenue > 0 else None
        
        # EV/EBITDA
        if data.market_cap and data.ebitda:
            total_debt = data.total_debt or 0
            cash = data.cash_and_equivalents or 0
            ev = data.market_cap + total_debt - cash
            ratios["ev_ebitda"] = round(ev / data.ebitda, 2) if data.ebitda > 0 else None
        
        # ROE
        if data.net_income and data.shareholders_equity:
            ratios["roe"] = round(data.net_income / data.shareholders_equity * 100, 2) if data.shareholders_equity > 0 else None
        
        # ROA
        if data.net_income and data.total_assets:
            ratios["roa"] = round(data.net_income / data.total_assets * 100, 2) if data.total_assets > 0 else None
        
        # Gross Margin
        if data.gross_profit and data.revenue:
            ratios["gross_margin"] = round(data.gross_profit / data.revenue * 100, 2) if data.revenue > 0 else None
        
        # Net Margin
        if data.net_income and data.revenue:
            ratios["net_margin"] = round(data.net_income / data.revenue * 100, 2) if data.revenue > 0 else None
        
        # Debt/Equity
        if data.total_debt and data.shareholders_equity:
            ratios["debt_to_equity"] = round(data.total_debt / data.shareholders_equity, 2) if data.shareholders_equity > 0 else None
        
        # Current Ratio
        if data.current_assets and data.current_liabilities:
            ratios["current_ratio"] = round(data.current_assets / data.current_liabilities, 2) if data.current_liabilities > 0 else None
        
        return ratios
