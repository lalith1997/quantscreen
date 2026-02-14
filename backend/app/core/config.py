"""
Application configuration using Pydantic settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "QuantScreen"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/quantscreen"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # External API Keys
    fmp_api_key: str = ""  # Financial Modeling Prep
    alpha_vantage_api_key: str = ""
    polygon_api_key: str = ""  # Optional, for Phase 2+
    
    # Redis (optional, for caching)
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
    ]
    
    @property
    def async_database_url(self) -> str:
        """Convert sync database URL to async."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
