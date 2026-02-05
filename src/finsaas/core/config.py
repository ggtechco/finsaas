"""Application configuration using Pydantic Settings."""

from decimal import Decimal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+psycopg://finsaas:finsaas@localhost:5432/finsaas"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Backtest defaults
    default_initial_capital: Decimal = Decimal("10000")
    default_commission_rate: Decimal = Decimal("0.001")
    default_slippage_rate: Decimal = Decimal("0.0005")

    # Optimization
    max_workers: int = Field(default=4, ge=1, le=64)

    # Series
    default_max_bars_back: int = Field(default=5000, ge=100)


def get_settings() -> Settings:
    """Create and return a Settings instance."""
    return Settings()
