# QuantScreen Pro — Product Specification

**Version:** 1.0  
**Date:** February 2026  
**Status:** Planning Phase  

---

## Executive Summary

QuantScreen Pro is a quantitative stock screening and research platform designed for serious investors who want institutional-grade analysis without institutional-grade costs. The platform combines fundamental analysis (value investing formulas), technical analysis (indicators and patterns), and risk metrics into a unified screening engine with real-time market data.

**Target Users:** Small investment team (2-5 people)  
**Primary Use Case:** Stock screening and research (no trading execution)  
**Markets:** US Stocks, International Markets, Cryptocurrency  

---

## Product Vision

### Core Value Proposition

> "Find undervalued, high-quality stocks using proven quantitative strategies—before the market does."

### Design Principles

1. **Accuracy over Speed** — Every calculation must be verifiable and correct
2. **Flexibility** — Users can combine any formulas into custom screens
3. **Transparency** — Show the math, not just the result
4. **Progressive Complexity** — Simple interface, powerful depth when needed

---

## Technical Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   React SPA     │  │   Mobile PWA    │  │  Future Native  │              │
│  │   (Primary)     │  │   (Optional)    │  │      Apps       │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┼────────────────────┼────────────────────┼────────────────────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                          ┌──────▼──────┐
                          │   API       │
                          │  Gateway    │
                          │  (nginx)    │
                          └──────┬──────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                         BACKEND LAYER                                        │
│                                │                                             │
│  ┌─────────────────────────────▼─────────────────────────────────┐          │
│  │                     FastAPI Application                        │          │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │          │
│  │  │  Screener   │  │  Formula    │  │  Real-time  │            │          │
│  │  │   Engine    │  │   Engine    │  │   Service   │            │          │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │          │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │          │
│  │  │    News     │  │  Backtest   │  │    User     │            │          │
│  │  │   Service   │  │   Engine    │  │   Service   │            │          │
│  │  └─────────────┘  └─────────────┘  └─────────────┘            │          │
│  └───────────────────────────────────────────────────────────────┘          │
│                                │                                             │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                          DATA LAYER                                          │
│                                │                                             │
│  ┌──────────────┐  ┌───────────▼───────────┐  ┌──────────────┐              │
│  │   Redis      │  │      PostgreSQL       │  │   TimescaleDB │              │
│  │   (Cache)    │  │   (Core Database)     │  │ (Time Series) │              │
│  └──────────────┘  └───────────────────────┘  └──────────────┘              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
┌────────────────────────────────┼────────────────────────────────────────────┐
│                      EXTERNAL DATA SOURCES                                   │
│                                │                                             │
│  ┌──────────────┐  ┌───────────▼───────────┐  ┌──────────────┐              │
│  │  Polygon.io  │  │    Alpha Vantage      │  │  CoinGecko   │              │
│  │  (Primary)   │  │    (Fallback)         │  │   (Crypto)   │              │
│  └──────────────┘  └───────────────────────┘  └──────────────┘              │
│                                                                              │
│  ┌──────────────┐  ┌───────────────────────┐  ┌──────────────┐              │
│  │ EOD Hist.    │  │   Financial Modeling  │  │   Finnhub    │              │
│  │ (Intl)       │  │      Prep (FMP)       │  │   (News)     │              │
│  └──────────────┘  └───────────────────────┘  └──────────────┘              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React 18 + TypeScript | Type safety, ecosystem, team familiarity |
| **UI Framework** | Tailwind CSS + Radix UI | Rapid development, accessibility |
| **Charts** | TradingView Lightweight Charts | Professional-grade, free |
| **State** | Zustand + React Query | Simple, performant |
| **Backend** | Python 3.12 + FastAPI | Financial libraries (pandas, numpy), async |
| **Database** | PostgreSQL 16 | Reliability, JSON support |
| **Time Series** | TimescaleDB | Efficient OHLCV storage |
| **Cache** | Redis 7 | Real-time data, session cache |
| **Task Queue** | Celery + Redis | Background data fetching |
| **Deployment** | Docker + Railway/Render | Simple deployment for small team |

---

## Data Strategy

### API Provider Matrix

| Data Type | Primary Provider | Fallback | Cost Estimate |
|-----------|-----------------|----------|---------------|
| US Stock Prices | Polygon.io Starter | Yahoo Finance (unofficial) | $29/mo |
| US Fundamentals | Financial Modeling Prep | SimFin Free | $19/mo |
| International | EOD Historical Data | Alpha Vantage | $20/mo |
| Crypto | CoinGecko Pro | Binance API | $0-129/mo |
| News | Finnhub Free | NewsAPI | $0 |
| Real-time Quotes | Polygon WebSocket | IEX Cloud | Included |

**Total Estimated Cost:** $70-200/month

### Data Refresh Strategy

| Data Type | Refresh Frequency | Method |
|-----------|------------------|--------|
| Fundamental Data | Daily (post-market) | Celery scheduled task |
| Price Data (EOD) | Daily (post-market) | Celery scheduled task |
| Price Data (Intraday) | 15-min delay | WebSocket stream |
| Crypto Prices | Real-time | WebSocket stream |
| News | Every 5 minutes | Polling |
| Calculated Metrics | On-demand + cached | Redis (1hr TTL) |

---

## Formula Engine Specification

### Category 1: Fundamental Valuation Formulas (6 Core Screeners)

#### 1.1 Joel Greenblatt's Magic Formula

**Purpose:** Identify undervalued companies with high returns on capital

**Components:**
```
Earnings Yield = EBIT / Enterprise Value
   where:
   - EBIT = Operating Income (or EBIT from income statement)
   - Enterprise Value = Market Cap + Total Debt - Cash

Return on Capital = EBIT / (Net Working Capital + Net Fixed Assets)
   where:
   - Net Working Capital = Current Assets - Current Liabilities
   - Net Fixed Assets = Total Assets - Current Assets - Intangible Assets

Magic Formula Rank = Rank(Earnings Yield) + Rank(Return on Capital)
   - Lower combined rank = better
```

**Implementation Notes:**
- Exclude financials (banks, insurance) and utilities
- Minimum market cap filter: $50M (configurable)
- Use trailing twelve months (TTM) data

#### 1.2 Acquirer's Multiple (Tobias Carlisle)

**Purpose:** Find deep value stocks trading below intrinsic value

**Formula:**
```
Acquirer's Multiple = Enterprise Value / Operating Earnings
   where:
   - Enterprise Value = Market Cap + Total Debt + Preferred Stock 
                        + Minority Interest - Cash
   - Operating Earnings = Operating Income (EBIT)

Interpretation:
   - Lower multiple = more undervalued
   - Typical range: 3x - 15x
   - Below 5x considered deep value
```

**Exclusions:** Financials, ADRs, OTC stocks

#### 1.3 Piotroski F-Score

**Purpose:** Assess financial strength of value stocks (0-9 scale)

**Nine Criteria (1 point each):**
```
PROFITABILITY (4 points)
1. ROA > 0                           → Net Income / Total Assets > 0
2. Operating Cash Flow > 0           → CFO > 0
3. ROA Improving                     → ROA(current) > ROA(prior year)
4. Accruals (Quality)                → CFO > Net Income

LEVERAGE & LIQUIDITY (3 points)
5. Leverage Decreasing               → LT Debt / Assets < Prior Year
6. Liquidity Improving               → Current Ratio > Prior Year
7. No Dilution                       → Shares Outstanding ≤ Prior Year

OPERATING EFFICIENCY (2 points)
8. Gross Margin Improving            → Gross Margin > Prior Year
9. Asset Turnover Improving          → Revenue/Assets > Prior Year

Score Interpretation:
   - 8-9: Strong (buy signal for value stocks)
   - 5-7: Moderate
   - 0-4: Weak (avoid or short)
```

#### 1.4 Altman Z-Score

**Purpose:** Predict bankruptcy risk

**Formula:**
```
Z-Score = 1.2×A + 1.4×B + 3.3×C + 0.6×D + 1.0×E

where:
   A = Working Capital / Total Assets
   B = Retained Earnings / Total Assets
   C = EBIT / Total Assets
   D = Market Value of Equity / Total Liabilities
   E = Sales / Total Assets

Interpretation:
   - Z > 2.99: Safe zone
   - 1.81 < Z < 2.99: Grey zone
   - Z < 1.81: Distress zone
```

#### 1.5 Beneish M-Score (NEW)

**Purpose:** Detect earnings manipulation and accounting fraud

**Formula:**
```
M-Score = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI 
          + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

where:
   DSRI = Days Sales Receivable Index
        = (Receivables/Sales)t / (Receivables/Sales)t-1
   
   GMI  = Gross Margin Index
        = Gross Margint-1 / Gross Margint
   
   AQI  = Asset Quality Index
        = [1 - (CA + PPE)/TA]t / [1 - (CA + PPE)/TA]t-1
   
   SGI  = Sales Growth Index
        = Salest / Salest-1
   
   DEPI = Depreciation Index
        = Depreciation Ratet-1 / Depreciation Ratet
   
   SGAI = SG&A Index
        = (SG&A/Sales)t / (SG&A/Sales)t-1
   
   TATA = Total Accruals to Total Assets
        = (Income from Continuing Ops - Cash from Ops) / Total Assets
   
   LVGI = Leverage Index
        = [(LTD + CL) / TA]t / [(LTD + CL) / TA]t-1

Interpretation:
   - M > -1.78: High probability of manipulation (RED FLAG)
   - M < -1.78: Low probability of manipulation (likely clean)
```

**Use Case:** Screen OUT stocks with M-Score > -1.78 before investing

#### 1.6 Sloan Accrual Ratio (NEW)

**Purpose:** Measure earnings quality — low accruals = higher quality

**Formula:**
```
Accrual Ratio = (Net Income - Operating Cash Flow) / Average Total Assets

   OR (Balance Sheet method):
   
Accrual Ratio = (ΔCurrent Assets - ΔCash - ΔCurrent Liabilities 
                 + ΔShort-term Debt - Depreciation) / Average Total Assets

Interpretation:
   - Ratio < -10%: High quality earnings (cash > reported income)
   - Ratio -10% to +10%: Normal
   - Ratio > +10%: Low quality earnings (RED FLAG)
   
   Lower (more negative) = Better quality
```

**Use Case:** Combine with F-Score. High F-Score + Low Accrual = Strong conviction

### Category 2: Technical Analysis Formulas

#### 2.1 Moving Averages

```python
# Simple Moving Average (SMA)
SMA(n) = sum(Close[i] for i in range(n)) / n

# Exponential Moving Average (EMA)
multiplier = 2 / (n + 1)
EMA(n) = (Close - EMA_prev) × multiplier + EMA_prev

# Common Periods: 10, 20, 50, 100, 200 days
```

#### 2.2 Relative Strength Index (RSI)

```python
# Step 1: Calculate price changes
change = Close[t] - Close[t-1]
gain = max(change, 0)
loss = abs(min(change, 0))

# Step 2: Calculate averages (typically 14 periods)
avg_gain = SMA(gains, 14)  # First calculation
avg_gain = (prev_avg_gain × 13 + current_gain) / 14  # Subsequent

# Step 3: Calculate RS and RSI
RS = avg_gain / avg_loss
RSI = 100 - (100 / (1 + RS))

# Interpretation:
#   RSI > 70: Overbought
#   RSI < 30: Oversold
```

#### 2.3 MACD (Moving Average Convergence Divergence)

```python
MACD_Line = EMA(12) - EMA(26)
Signal_Line = EMA(MACD_Line, 9)
MACD_Histogram = MACD_Line - Signal_Line

# Signals:
#   MACD crosses above Signal: Bullish
#   MACD crosses below Signal: Bearish
```

#### 2.4 Bollinger Bands

```python
Middle_Band = SMA(Close, 20)
Upper_Band = Middle_Band + (2 × StdDev(Close, 20))
Lower_Band = Middle_Band - (2 × StdDev(Close, 20))

Bandwidth = (Upper - Lower) / Middle
%B = (Close - Lower) / (Upper - Lower)
```

#### 2.5 Average True Range (ATR)

```python
True_Range = max(
    High - Low,
    abs(High - Previous_Close),
    abs(Low - Previous_Close)
)

ATR = SMA(True_Range, 14)  # or Wilder's smoothing
```

#### 2.6 ADX — Average Directional Index (NEW)

**Purpose:** Measure trend strength (not direction). Essential filter before following trend signals.

```python
# Step 1: Calculate Directional Movement
+DM = High[t] - High[t-1] if (High[t] - High[t-1]) > (Low[t-1] - Low[t]) else 0
-DM = Low[t-1] - Low[t] if (Low[t-1] - Low[t]) > (High[t] - High[t-1]) else 0

# Step 2: Smooth with Wilder's method (14 periods typical)
+DI = 100 × Smoothed(+DM) / ATR
-DI = 100 × Smoothed(-DM) / ATR

# Step 3: Calculate ADX
DX = 100 × |+DI - -DI| / (+DI + -DI)
ADX = Wilder_Smooth(DX, 14)

Interpretation:
   - ADX < 20: No trend (range-bound) — avoid trend strategies
   - ADX 20-25: Trend emerging
   - ADX 25-50: Strong trend — trend strategies work well
   - ADX > 50: Extremely strong trend (rare)
   
   +DI > -DI: Uptrend
   -DI > +DI: Downtrend
```

**Use Case:** Only follow RSI/MACD signals when ADX > 25 (confirms trend exists)

#### 2.7 Ichimoku Cloud (NEW)

**Purpose:** All-in-one trend system showing support, resistance, momentum, and trend direction.

```python
# Five Components (default periods: 9, 26, 52)
Tenkan-sen (Conversion Line) = (Highest High[9] + Lowest Low[9]) / 2
Kijun-sen (Base Line) = (Highest High[26] + Lowest Low[26]) / 2
Senkou Span A (Leading Span A) = (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
Senkou Span B (Leading Span B) = (Highest High[52] + Lowest Low[52]) / 2, plotted 26 periods ahead
Chikou Span (Lagging Span) = Close, plotted 26 periods behind

The Cloud (Kumo) = Area between Senkou Span A and Senkou Span B

Interpretation:
   BULLISH SIGNALS:
   - Price above the Cloud
   - Tenkan-sen crosses above Kijun-sen (above cloud = strong)
   - Cloud is green (Span A > Span B)
   - Chikou Span above price from 26 periods ago
   
   BEARISH SIGNALS:
   - Price below the Cloud
   - Tenkan-sen crosses below Kijun-sen (below cloud = strong)
   - Cloud is red (Span B > Span A)
   - Chikou Span below price from 26 periods ago
   
   SUPPORT/RESISTANCE:
   - Cloud edges act as support (in uptrend) or resistance (in downtrend)
   - Thicker cloud = stronger support/resistance
```

**Use Case:** For long-term investors, focus on price position relative to cloud and cloud color for overall trend assessment.

### Category 3: Risk & Performance Metrics

#### 3.1 Sharpe Ratio

```python
Sharpe = (Portfolio_Return - Risk_Free_Rate) / StdDev(Portfolio_Returns)

# Annualized (daily data):
Annualized_Return = mean(daily_returns) × 252
Annualized_StdDev = std(daily_returns) × sqrt(252)
Sharpe_Annualized = (Annualized_Return - Risk_Free_Rate) / Annualized_StdDev
```

#### 3.2 Sortino Ratio

```python
Downside_Returns = [r for r in returns if r < target_return]
Downside_Deviation = sqrt(mean([r² for r in Downside_Returns]))

Sortino = (Portfolio_Return - Target_Return) / Downside_Deviation
```

#### 3.3 Maximum Drawdown

```python
def max_drawdown(prices):
    peak = prices[0]
    max_dd = 0
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        max_dd = max(max_dd, dd)
    return max_dd
```

#### 3.4 Beta & Alpha

```python
# Beta: Sensitivity to market
Beta = Covariance(Stock_Returns, Market_Returns) / Variance(Market_Returns)

# Alpha: Excess return vs expected (CAPM)
Expected_Return = Risk_Free + Beta × (Market_Return - Risk_Free)
Alpha = Actual_Return - Expected_Return
```

### Category 4: Valuation Ratios

```python
# Price Ratios
P/E = Price / Earnings_Per_Share
P/B = Price / Book_Value_Per_Share
P/S = Market_Cap / Revenue
P/CF = Price / Cash_Flow_Per_Share
P/FCF = Price / Free_Cash_Flow_Per_Share

# Enterprise Ratios
EV/EBITDA = Enterprise_Value / EBITDA
EV/Sales = Enterprise_Value / Revenue
EV/FCF = Enterprise_Value / Free_Cash_Flow

# Profitability
ROE = Net_Income / Shareholders_Equity
ROA = Net_Income / Total_Assets
ROIC = NOPAT / Invested_Capital
Gross_Margin = (Revenue - COGS) / Revenue
Net_Margin = Net_Income / Revenue

# Dividend
Dividend_Yield = Annual_Dividend / Price
Payout_Ratio = Dividends / Net_Income
```

---

## Screening Engine Design

### Filter System

The screener allows combining any metrics with boolean logic:

```typescript
interface ScreenerFilter {
  metric: string;          // e.g., "pe_ratio", "magic_formula_rank"
  operator: ">" | "<" | ">=" | "<=" | "==" | "between" | "in";
  value: number | number[] | string[];
  
  // Optional metadata
  percentile?: boolean;    // Use percentile instead of absolute
  sector_relative?: boolean; // Compare within sector
}

interface Screen {
  id: string;
  name: string;
  filters: ScreenerFilter[];
  logic: "AND" | "OR";     // How to combine filters
  sort_by: string;
  sort_order: "asc" | "desc";
  limit: number;
}
```

### Pre-built Screens

1. **Magic Formula Top 50**
   - Exclude: Financials, Utilities, ADRs
   - Market Cap > $50M
   - Sort by: Magic Formula Rank (ascending)
   - Limit: 50

2. **Deep Value (Acquirer's Multiple)**
   - Acquirer's Multiple < 8
   - Market Cap > $100M
   - F-Score >= 5
   - Sort by: Acquirer's Multiple (ascending)

3. **Quality at Reasonable Price (GARP)**
   - PEG Ratio < 1.5
   - ROE > 15%
   - Debt/Equity < 0.5
   - Revenue Growth (YoY) > 10%

4. **Dividend Champions**
   - Dividend Yield > 3%
   - Payout Ratio < 60%
   - Dividend Growth (5yr) > 5%
   - F-Score >= 6

5. **Momentum + Quality**
   - RSI(14) between 40-70
   - Price > SMA(200)
   - ROE > 15%
   - Revenue Growth > 0

---

## Timing Signals System (Long-Term Investor Focus)

### Overview

Timing signals help answer: **"Is now a good time to buy/sell this stock?"**

Unlike trading signals (buy Monday, sell Friday), these are designed for **long-term position management**.

### Signal Categories

#### 1. Valuation Timing

```
Current P/E vs Historical:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current P/E:      18.5
5-Year Avg P/E:   22.3
5-Year Low P/E:   14.2
5-Year High P/E:  28.7

Percentile:       32nd (historically cheap)
Signal:           🟢 UNDERVALUED

Fair Value Est:   $185 (based on avg P/E × current EPS)
Current Price:    $172
Discount:         -7% (buying below fair value)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 2. Technical Timing

| Indicator | Reading | Signal | Meaning |
|-----------|---------|--------|---------|
| RSI (14) | 28 | 🟢 Oversold | Good entry zone |
| Price vs SMA200 | -5% below | 🟢 Pullback | Buying the dip |
| ADX | 32 | ✓ Trending | Trend signals valid |
| Ichimoku | Below cloud | 🔴 Downtrend | Wait or scale in slowly |

#### 3. Combined Entry Score

```python
Entry Score Calculation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Valuation Score (40% weight):
   - P/E percentile vs history
   - P/B percentile vs history
   - Discount to fair value estimate

Technical Score (30% weight):
   - RSI position (oversold = better)
   - Price vs 200-day MA
   - Ichimoku cloud position

Quality Score (30% weight):
   - F-Score (higher = better)
   - M-Score (clean = better)  
   - Accrual Ratio (lower = better)

Final Score: 0-100
   85-100: 🟢 Strong Buy Zone
   70-84:  🟢 Good Entry
   50-69:  🟡 Fair / Hold
   30-49:  🟡 Elevated / Wait
   0-29:   🔴 Avoid / Take Profits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Alert Types

| Alert | Trigger | Use Case |
|-------|---------|----------|
| **Price Target** | Price crosses threshold | "Buy MSFT if it drops to $350" |
| **Valuation Alert** | P/E drops below X | "Alert when P/E < 15" |
| **Quality Warning** | F-Score drops below 5 | "Warn if fundamentals weaken" |
| **Fraud Warning** | M-Score exceeds -1.78 | "Alert if manipulation detected" |
| **Technical Entry** | RSI < 30 + Price < SMA200 | "Oversold pullback alert" |
| **Trend Change** | Price crosses Ichimoku cloud | "Trend reversal warning" |

---

## Backtesting Engine

### Purpose

Validate that your screening approach works before committing capital.

### Capabilities

```
Test Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Screen:           Magic Formula Top 30
Rebalance:        Annually (January)
Period:           2005-2024 (20 years)
Starting Capital: $100,000
Benchmark:        S&P 500
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    Strategy    S&P 500
Total Return:       +847%       +412%
CAGR:               12.3%       8.7%
Sharpe Ratio:       0.72        0.58
Max Drawdown:       -38%        -51%
Best Year:          +47%        +32%
Worst Year:         -38%        -37%
Years Beating SPY:  14/20 (70%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Yearly Breakdown:
2005: +18.2%  (SPY: +4.9%)   ✓
2006: +22.4%  (SPY: +15.8%)  ✓
2007: +8.1%   (SPY: +5.5%)   ✓
2008: -38.2%  (SPY: -37.0%)  ✗
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Backtest Options

| Option | Choices |
|--------|---------|
| **Rebalance Frequency** | Monthly, Quarterly, Semi-annually, Annually |
| **Position Sizing** | Equal weight, Market cap weight, Inverse volatility |
| **Universe** | All US stocks, Large cap only, Exclude financials |
| **Filters** | Add F-Score > 5, Add M-Score filter, etc. |

---

### Core Tables

```sql
-- Companies master table
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    exchange VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    country VARCHAR(50),
    currency VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fundamental data (quarterly/annual)
CREATE TABLE fundamentals (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    period_end DATE NOT NULL,
    period_type VARCHAR(10), -- 'Q1', 'Q2', 'Q3', 'Q4', 'FY'
    
    -- Income Statement
    revenue NUMERIC,
    cost_of_revenue NUMERIC,
    gross_profit NUMERIC,
    operating_income NUMERIC,
    ebit NUMERIC,
    ebitda NUMERIC,
    net_income NUMERIC,
    eps NUMERIC,
    eps_diluted NUMERIC,
    
    -- Balance Sheet
    total_assets NUMERIC,
    current_assets NUMERIC,
    total_liabilities NUMERIC,
    current_liabilities NUMERIC,
    total_debt NUMERIC,
    long_term_debt NUMERIC,
    shareholders_equity NUMERIC,
    retained_earnings NUMERIC,
    cash_and_equivalents NUMERIC,
    
    -- Cash Flow
    operating_cash_flow NUMERIC,
    capital_expenditures NUMERIC,
    free_cash_flow NUMERIC,
    dividends_paid NUMERIC,
    
    -- Shares
    shares_outstanding BIGINT,
    shares_outstanding_diluted BIGINT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, period_end, period_type)
);

-- Price data (TimescaleDB hypertable)
CREATE TABLE prices (
    company_id INT REFERENCES companies(id),
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    adjusted_close NUMERIC,
    volume BIGINT,
    PRIMARY KEY (company_id, date)
);
SELECT create_hypertable('prices', 'date');

-- Calculated metrics (cached)
CREATE TABLE metrics_cache (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    rank_value INT,               -- Percentile rank (1-100)
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, metric_name)
);

-- User screens
CREATE TABLE screens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User watchlists
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    tickers TEXT[] NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    company_id INT REFERENCES companies(id),
    condition JSONB NOT NULL,  -- e.g., {"metric": "price", "op": "<", "value": 100}
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Endpoints

### Core REST API

```
Authentication
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/refresh
DELETE /api/auth/logout

Companies
GET    /api/companies                    # List with filters
GET    /api/companies/:ticker            # Company detail
GET    /api/companies/:ticker/fundamentals
GET    /api/companies/:ticker/prices
GET    /api/companies/:ticker/metrics

Screener
POST   /api/screener/run                 # Run custom screen
GET    /api/screener/presets             # Get pre-built screens
GET    /api/screener/presets/:id/run     # Run a preset

Metrics
GET    /api/metrics/calculate/:ticker    # Calculate all metrics
GET    /api/metrics/rankings             # Get metric rankings

Watchlists
GET    /api/watchlists
POST   /api/watchlists
PUT    /api/watchlists/:id
DELETE /api/watchlists/:id

Alerts
GET    /api/alerts
POST   /api/alerts
DELETE /api/alerts/:id

Market Data
GET    /api/market/quote/:ticker         # Real-time quote
GET    /api/market/news                  # Latest news
WS     /api/market/stream                # WebSocket for real-time

Crypto
GET    /api/crypto/list
GET    /api/crypto/:symbol/price
GET    /api/crypto/:symbol/metrics
```

---

## UI/UX Design

### Page Structure

```
1. Dashboard (Home)
   ├── Portfolio summary widget
   ├── Watchlist quick view
   ├── Top gainers/losers
   ├── Recent news feed
   └── Market indices

2. Screener
   ├── Filter builder (drag & drop)
   ├── Preset screens sidebar
   ├── Results table (sortable)
   ├── Quick actions (add to watchlist, view detail)
   └── Export options (CSV, PDF)

3. Stock Detail Page
   ├── Header: Price, change, market cap
   ├── Interactive chart (TradingView)
   ├── Tabs: Overview | Financials | Metrics | News
   ├── Fundamental metrics grid
   ├── Technical indicators panel
   └── Similar stocks / competitors

4. Watchlists
   ├── Multiple lists support
   ├── Real-time price updates
   ├── Bulk actions
   └── Performance tracking

5. Backtest (Phase 3)
   ├── Strategy builder
   ├── Historical simulation
   ├── Performance analytics
   └── Compare strategies

6. Settings
   ├── Account management
   ├── API key configuration
   ├── Alert preferences
   └── Display preferences
```

### Design System

**Colors (Dark Mode Primary):**
```css
--bg-primary: #0f0f0f;
--bg-secondary: #1a1a1a;
--bg-tertiary: #252525;
--text-primary: #ffffff;
--text-secondary: #a0a0a0;
--accent-green: #00d26a;
--accent-red: #ff4757;
--accent-blue: #0095ff;
--accent-yellow: #ffc107;
```

**Typography:**
- Headings: Inter (or JetBrains Mono for numbers)
- Body: Inter
- Monospace/Data: JetBrains Mono

---

## Development Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goal:** Core infrastructure + basic screening

| Week | Deliverables |
|------|--------------|
| 1 | Project setup, database schema, API scaffolding |
| 2 | Data ingestion pipeline (Polygon, FMP) for US stocks |
| 3 | Formula engine (Magic Formula, Acquirer's Multiple, F-Score, M-Score, Accrual Ratio, Z-Score) |
| 4 | Basic screener UI + results table |

**Phase 1 Milestone:** Run all 6 core screens on US stocks

---

### Phase 2: Analysis & Validation (Weeks 5-8)

**Goal:** Complete analysis toolkit + backtesting + timing signals

| Week | Deliverables |
|------|--------------|
| 5 | All fundamental ratios (P/E, P/B, ROE, etc.) + Stock detail page |
| 6 | Technical indicators (RSI, MACD, Bollinger, ADX, Ichimoku) + TradingView chart |
| 7 | **Backtesting engine** — validate screens against historical data |
| 8 | **Timing signals** + Price/fundamental alerts + Watchlists |

**Timing Signals Include:**
- Entry timing: RSI oversold/overbought, price vs moving averages, Ichimoku position
- Valuation context: Current P/E vs 5-year average, discount to fair value estimate
- Combined score: "Good entry", "Fair", "Wait for pullback"

**Backtesting Capabilities:**
- Test any screen historically (5-20 years)
- Compare vs S&P 500 benchmark  
- Annual returns, max drawdown, Sharpe ratio
- Win rate by year

**Phase 2 Milestone:** Full stock analysis workflow with validated screens

---

### Phase 3: Scale & Real-time (Weeks 9-12)

**Goal:** International markets + real-time features

| Week | Deliverables |
|------|--------------|
| 9 | International stocks integration (EOD Historical Data) |
| 10 | Crypto integration (CoinGecko) |
| 11 | Real-time price updates (WebSocket) |
| 12 | News feed integration + performance dashboards |

**Phase 3 Milestone:** Multi-market screening with real-time data

---

### Phase 4: Team & Polish (Weeks 13-16)

**Goal:** Team collaboration + production hardening

| Week | Deliverables |
|------|--------------|
| 13 | Team features (shared screens, watchlists, notes) |
| 14 | Portfolio tracking (track your positions vs benchmarks) |
| 15 | Advanced alerts (F-Score drops, M-Score warnings, price targets) |
| 16 | Performance optimization, documentation, deployment |

**Phase 4 Milestone:** Production-ready platform for team use

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data API costs exceed budget | High | Build multi-provider fallback; cache aggressively |
| Data quality issues | High | Validate all calculations; add data quality checks |
| Scope creep | Medium | Strict phase boundaries; MVP first |
| Real-time complexity | Medium | Start with delayed quotes; add real-time later |
| User adoption | Low | Build for team needs; iterate based on feedback |

---

## Success Metrics

**Phase 1 Success:**
- [ ] Can run all 6 core screens in < 3 seconds
- [ ] Data accuracy validated against known sources (Bloomberg, Yahoo Finance)
- [ ] M-Score correctly flags known fraud cases (Enron, Wirecard test data)

**Phase 2 Success:**
- [ ] Full stock analysis in < 5 clicks
- [ ] All F-Score components calculating correctly
- [ ] Backtest engine produces results matching academic papers
- [ ] Timing signals provide actionable entry/exit guidance
- [ ] Alerts trigger correctly within 5 minutes of condition

**Phase 3 Success:**
- [ ] 5000+ international stocks available
- [ ] Real-time quotes updating < 1 second latency
- [ ] Crypto metrics calculating correctly

**Phase 4 Success:**
- [ ] Team using daily for research
- [ ] Shared screens working across team members
- [ ] Portfolio tracking accurate to within 0.1%

---

## Appendix A: Complete Metric List

### Core Screeners (6)
- Magic Formula (Greenblatt)
- Acquirer's Multiple (Carlisle)
- Piotroski F-Score
- Altman Z-Score
- Beneish M-Score (fraud detection)
- Sloan Accrual Ratio (earnings quality)

### Fundamental Metrics (70+)
- Valuation: P/E, Forward P/E, PEG, P/B, P/S, P/CF, P/FCF, EV/EBITDA, EV/Sales, EV/FCF
- Profitability: ROE, ROA, ROIC, Gross Margin, Operating Margin, Net Margin, FCF Margin
- Growth: Revenue Growth (QoQ, YoY, 3Y, 5Y), EPS Growth, FCF Growth
- Financial Health: Debt/Equity, Debt/Assets, Current Ratio, Quick Ratio, Interest Coverage
- Efficiency: Asset Turnover, Inventory Turnover, Receivables Turnover
- Dividends: Yield, Payout Ratio, Dividend Growth Rate

### Technical Indicators (32+)
- Trend: SMA (10, 20, 50, 100, 200), EMA, MACD, **Ichimoku Cloud**
- Momentum: RSI, Stochastic, Williams %R, CCI, ROC
- Volatility: Bollinger Bands, ATR, Standard Deviation
- Volume: OBV, VWAP, A/D Line, CMF
- Trend Strength: **ADX** (Average Directional Index)

### Risk Metrics (10+)
- Sharpe Ratio, Sortino Ratio, Treynor Ratio
- Beta, Alpha, R-Squared
- Max Drawdown, VaR, Volatility (annualized)

---

## Appendix B: File Structure

```
quantscreen/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   ├── screener/
│   │   │   ├── stock/
│   │   │   └── ui/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── stores/
│   │   └── utils/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── data_providers/
│   │   │   ├── formula_engine/
│   │   │   └── screener/
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   └── requirements.txt
│
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
│
└── docs/
    ├── api.md
    ├── formulas.md
    └── setup.md
```

---

## Next Steps

1. **Approve this specification** — review and confirm priorities
2. **Set up development environment** — Docker, databases, API keys
3. **Begin Phase 1** — Start with data pipeline and core formulas

---

*Document prepared for QuantScreen Pro development team*
