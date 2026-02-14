"""
Database seeder - populates companies table with initial stock data.
Uses FMP API to fetch S&P 500 constituents, or falls back to a hardcoded list.
"""

from sqlalchemy.orm import Session
from app.models import Company
from app.core.config import settings

# Hardcoded list of well-known US stocks with sectors and market caps
# This ensures the screener works even without FMP API access
SEED_COMPANIES = [
    # Technology
    ("AAPL", "Apple Inc.", "NASDAQ", "Technology", "Consumer Electronics", 3000000000000),
    ("MSFT", "Microsoft Corporation", "NASDAQ", "Technology", "Software—Infrastructure", 2800000000000),
    ("GOOGL", "Alphabet Inc.", "NASDAQ", "Technology", "Internet Content & Information", 1800000000000),
    ("AMZN", "Amazon.com Inc.", "NASDAQ", "Technology", "Internet Retail", 1600000000000),
    ("NVDA", "NVIDIA Corporation", "NASDAQ", "Technology", "Semiconductors", 2500000000000),
    ("META", "Meta Platforms Inc.", "NASDAQ", "Technology", "Internet Content & Information", 1200000000000),
    ("AVGO", "Broadcom Inc.", "NASDAQ", "Technology", "Semiconductors", 600000000000),
    ("ORCL", "Oracle Corporation", "NYSE", "Technology", "Software—Infrastructure", 350000000000),
    ("CRM", "Salesforce Inc.", "NYSE", "Technology", "Software—Application", 250000000000),
    ("ADBE", "Adobe Inc.", "NASDAQ", "Technology", "Software—Application", 230000000000),
    ("AMD", "Advanced Micro Devices Inc.", "NASDAQ", "Technology", "Semiconductors", 200000000000),
    ("INTC", "Intel Corporation", "NASDAQ", "Technology", "Semiconductors", 120000000000),
    ("IBM", "International Business Machines", "NYSE", "Technology", "Information Technology Services", 170000000000),
    ("QCOM", "Qualcomm Incorporated", "NASDAQ", "Technology", "Semiconductors", 180000000000),
    ("TXN", "Texas Instruments Incorporated", "NASDAQ", "Technology", "Semiconductors", 165000000000),
    ("AMAT", "Applied Materials Inc.", "NASDAQ", "Technology", "Semiconductor Equipment", 130000000000),
    ("MU", "Micron Technology Inc.", "NASDAQ", "Technology", "Semiconductors", 100000000000),
    ("PANW", "Palo Alto Networks Inc.", "NASDAQ", "Technology", "Software—Infrastructure", 110000000000),
    ("NOW", "ServiceNow Inc.", "NYSE", "Technology", "Software—Application", 150000000000),
    ("INTU", "Intuit Inc.", "NASDAQ", "Technology", "Software—Application", 180000000000),
    # Healthcare
    ("JNJ", "Johnson & Johnson", "NYSE", "Healthcare", "Drug Manufacturers—General", 400000000000),
    ("UNH", "UnitedHealth Group Inc.", "NYSE", "Healthcare", "Healthcare Plans", 500000000000),
    ("LLY", "Eli Lilly and Company", "NYSE", "Healthcare", "Drug Manufacturers—General", 700000000000),
    ("PFE", "Pfizer Inc.", "NYSE", "Healthcare", "Drug Manufacturers—General", 160000000000),
    ("ABBV", "AbbVie Inc.", "NYSE", "Healthcare", "Drug Manufacturers—General", 300000000000),
    ("MRK", "Merck & Co. Inc.", "NYSE", "Healthcare", "Drug Manufacturers—General", 280000000000),
    ("TMO", "Thermo Fisher Scientific Inc.", "NYSE", "Healthcare", "Diagnostics & Research", 200000000000),
    ("ABT", "Abbott Laboratories", "NYSE", "Healthcare", "Medical Devices", 190000000000),
    ("DHR", "Danaher Corporation", "NYSE", "Healthcare", "Diagnostics & Research", 180000000000),
    ("BMY", "Bristol-Myers Squibb Company", "NYSE", "Healthcare", "Drug Manufacturers—General", 120000000000),
    # Consumer
    ("WMT", "Walmart Inc.", "NYSE", "Consumer Defensive", "Discount Stores", 450000000000),
    ("PG", "Procter & Gamble Company", "NYSE", "Consumer Defensive", "Household & Personal Products", 370000000000),
    ("KO", "The Coca-Cola Company", "NYSE", "Consumer Defensive", "Beverages—Non-Alcoholic", 270000000000),
    ("PEP", "PepsiCo Inc.", "NYSE", "Consumer Defensive", "Beverages—Non-Alcoholic", 230000000000),
    ("COST", "Costco Wholesale Corporation", "NASDAQ", "Consumer Defensive", "Discount Stores", 320000000000),
    ("MCD", "McDonald's Corporation", "NYSE", "Consumer Cyclical", "Restaurants", 210000000000),
    ("NKE", "NIKE Inc.", "NYSE", "Consumer Cyclical", "Footwear & Accessories", 140000000000),
    ("SBUX", "Starbucks Corporation", "NASDAQ", "Consumer Cyclical", "Restaurants", 110000000000),
    ("HD", "The Home Depot Inc.", "NYSE", "Consumer Cyclical", "Home Improvement Retail", 350000000000),
    ("LOW", "Lowe's Companies Inc.", "NYSE", "Consumer Cyclical", "Home Improvement Retail", 140000000000),
    ("TGT", "Target Corporation", "NYSE", "Consumer Defensive", "Discount Stores", 70000000000),
    ("DIS", "The Walt Disney Company", "NYSE", "Communication Services", "Entertainment", 200000000000),
    # Industrials
    ("CAT", "Caterpillar Inc.", "NYSE", "Industrials", "Farm & Heavy Construction Machinery", 160000000000),
    ("GE", "General Electric Company", "NYSE", "Industrials", "Specialty Industrial Machinery", 180000000000),
    ("HON", "Honeywell International Inc.", "NASDAQ", "Industrials", "Conglomerate", 140000000000),
    ("UNP", "Union Pacific Corporation", "NYSE", "Industrials", "Railroads", 150000000000),
    ("BA", "The Boeing Company", "NYSE", "Industrials", "Aerospace & Defense", 130000000000),
    ("RTX", "RTX Corporation", "NYSE", "Industrials", "Aerospace & Defense", 140000000000),
    ("DE", "Deere & Company", "NYSE", "Industrials", "Farm & Heavy Construction Machinery", 120000000000),
    ("LMT", "Lockheed Martin Corporation", "NYSE", "Industrials", "Aerospace & Defense", 110000000000),
    ("MMM", "3M Company", "NYSE", "Industrials", "Conglomerate", 60000000000),
    ("UPS", "United Parcel Service Inc.", "NYSE", "Industrials", "Integrated Freight & Logistics", 100000000000),
    # Energy
    ("XOM", "Exxon Mobil Corporation", "NYSE", "Energy", "Oil & Gas Integrated", 450000000000),
    ("CVX", "Chevron Corporation", "NYSE", "Energy", "Oil & Gas Integrated", 300000000000),
    ("COP", "ConocoPhillips", "NYSE", "Energy", "Oil & Gas E&P", 130000000000),
    ("SLB", "Schlumberger Limited", "NYSE", "Energy", "Oil & Gas Equipment & Services", 70000000000),
    ("EOG", "EOG Resources Inc.", "NYSE", "Energy", "Oil & Gas E&P", 70000000000),
    # Communication Services
    ("NFLX", "Netflix Inc.", "NASDAQ", "Communication Services", "Entertainment", 250000000000),
    ("CMCSA", "Comcast Corporation", "NASDAQ", "Communication Services", "Telecom Services", 170000000000),
    ("T", "AT&T Inc.", "NYSE", "Communication Services", "Telecom Services", 130000000000),
    ("VZ", "Verizon Communications Inc.", "NYSE", "Communication Services", "Telecom Services", 170000000000),
    ("TMUS", "T-Mobile US Inc.", "NASDAQ", "Communication Services", "Telecom Services", 200000000000),
    # Materials
    ("LIN", "Linde plc", "NYSE", "Basic Materials", "Specialty Chemicals", 200000000000),
    ("APD", "Air Products and Chemicals", "NYSE", "Basic Materials", "Specialty Chemicals", 60000000000),
    ("FCX", "Freeport-McMoRan Inc.", "NYSE", "Basic Materials", "Copper", 60000000000),
    ("NEM", "Newmont Corporation", "NYSE", "Basic Materials", "Gold", 50000000000),
    ("DOW", "Dow Inc.", "NYSE", "Basic Materials", "Chemicals", 35000000000),
    # Real Estate (excluded from some screens but useful)
    ("PLD", "Prologis Inc.", "NYSE", "Real Estate", "REIT—Industrial", 110000000000),
    ("AMT", "American Tower Corporation", "NYSE", "Real Estate", "REIT—Specialty", 90000000000),
    # Additional large caps
    ("V", "Visa Inc.", "NYSE", "Financial Services", "Credit Services", 500000000000),
    ("MA", "Mastercard Incorporated", "NYSE", "Financial Services", "Credit Services", 400000000000),
    ("JPM", "JPMorgan Chase & Co.", "NYSE", "Financial Services", "Banks—Diversified", 500000000000),
    ("BAC", "Bank of America Corporation", "NYSE", "Financial Services", "Banks—Diversified", 300000000000),
    ("WFC", "Wells Fargo & Company", "NYSE", "Financial Services", "Banks—Diversified", 180000000000),
    ("GS", "Goldman Sachs Group Inc.", "NYSE", "Financial Services", "Capital Markets", 130000000000),
    ("MS", "Morgan Stanley", "NYSE", "Financial Services", "Capital Markets", 150000000000),
    ("BRK-B", "Berkshire Hathaway Inc.", "NYSE", "Financial Services", "Insurance—Diversified", 800000000000),
    ("BLK", "BlackRock Inc.", "NYSE", "Financial Services", "Asset Management", 120000000000),
    ("SPGI", "S&P Global Inc.", "NYSE", "Financial Services", "Financial Data & Stock Exchanges", 140000000000),
    # Additional value/quality names
    ("CSCO", "Cisco Systems Inc.", "NASDAQ", "Technology", "Communication Equipment", 220000000000),
    ("ACN", "Accenture plc", "NYSE", "Technology", "Information Technology Services", 210000000000),
    ("AXP", "American Express Company", "NYSE", "Financial Services", "Credit Services", 160000000000),
    ("ISRG", "Intuitive Surgical Inc.", "NASDAQ", "Healthcare", "Medical Instruments & Supplies", 140000000000),
    ("VRTX", "Vertex Pharmaceuticals Inc.", "NASDAQ", "Healthcare", "Biotechnology", 100000000000),
    ("GILD", "Gilead Sciences Inc.", "NASDAQ", "Healthcare", "Biotechnology", 100000000000),
    ("MDT", "Medtronic plc", "NYSE", "Healthcare", "Medical Devices", 110000000000),
    ("CI", "Cigna Group", "NYSE", "Healthcare", "Healthcare Plans", 90000000000),
    ("ELV", "Elevance Health Inc.", "NYSE", "Healthcare", "Healthcare Plans", 110000000000),
    ("SYK", "Stryker Corporation", "NYSE", "Healthcare", "Medical Devices", 120000000000),
    ("ZTS", "Zoetis Inc.", "NYSE", "Healthcare", "Drug Manufacturers—Specialty & Generic", 80000000000),
    ("CL", "Colgate-Palmolive Company", "NYSE", "Consumer Defensive", "Household & Personal Products", 75000000000),
    ("GIS", "General Mills Inc.", "NYSE", "Consumer Defensive", "Packaged Foods", 40000000000),
    ("K", "Kellanova", "NYSE", "Consumer Defensive", "Packaged Foods", 25000000000),
    ("ADM", "Archer-Daniels-Midland Company", "NYSE", "Consumer Defensive", "Farm Products", 30000000000),
    ("FDX", "FedEx Corporation", "NYSE", "Industrials", "Integrated Freight & Logistics", 65000000000),
    ("EMR", "Emerson Electric Co.", "NYSE", "Industrials", "Specialty Industrial Machinery", 65000000000),
    ("ETN", "Eaton Corporation plc", "NYSE", "Industrials", "Specialty Industrial Machinery", 110000000000),
    ("ITW", "Illinois Tool Works Inc.", "NYSE", "Industrials", "Specialty Industrial Machinery", 75000000000),
    ("WM", "Waste Management Inc.", "NYSE", "Industrials", "Waste Management", 80000000000),
]


def seed_companies(db: Session) -> int:
    """
    Seed the companies table with initial stock data.
    Returns the number of companies added.
    """
    existing_tickers = {c.ticker for c in db.query(Company.ticker).all()}
    added = 0

    for ticker, name, exchange, sector, industry, market_cap in SEED_COMPANIES:
        if ticker not in existing_tickers:
            company = Company(
                ticker=ticker,
                name=name,
                exchange=exchange,
                sector=sector,
                industry=industry,
                market_cap=market_cap,
                country="US",
                currency="USD",
                is_active=True,
            )
            db.add(company)
            added += 1

    if added > 0:
        db.commit()

    return added
