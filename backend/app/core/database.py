"""
Database connection and session management.
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures session is closed after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations():
    """Add missing columns to existing tables (lightweight migration)."""
    migrations = [
        # (table, column, SQL type, default)
        ("companies", "is_etf", "BOOLEAN", "FALSE"),
        ("daily_picks", "earnings_date", "DATE", None),
        ("daily_picks", "earnings_proximity", "VARCHAR(20)", None),
        ("daily_picks", "eps_estimated", "NUMERIC(12,4)", None),
    ]
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, column, sql_type, default in migrations:
            if not inspector.has_table(table):
                continue
            existing = [c["name"] for c in inspector.get_columns(table)]
            if column not in existing:
                default_clause = f" DEFAULT {default}" if default else ""
                conn.execute(text(
                    f'ALTER TABLE {table} ADD COLUMN {column} {sql_type}{default_clause}'
                ))
                print(f"  Migration: added {table}.{column}")


def init_db():
    """Initialize database tables and run migrations."""
    Base.metadata.create_all(bind=engine)
    _run_migrations()
