"""Application configuration loaded from environment variables / `.env`.

Uses pydantic-settings so configuration is validated and typed. Access the
singleton via :func:`get_settings` (cached) so the `.env` file is parsed once.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, overridable via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application metadata ---
    app_name: str = "TerraSense NER API"
    app_description: str = (
        "AI-Based Landslide Early Warning & Risk Monitoring System — "
        "backend API for the North Eastern Region (NER)."
    )
    version: str = "0.1.0"
    environment: str = "development"

    # --- API ---
    # Mounted prefix for all routes; must match the frontend VITE_API_BASE_URL path.
    api_prefix: str = "/api"

    # --- Logging ---
    log_level: str = "INFO"

    # --- CORS ---
    # NoDecode: keep pydantic-settings from JSON-parsing the env value so the
    # validator below can accept a plain comma-separated string.
    backend_cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- Database (Neon PostgreSQL + PostGIS) ---
    # SQLAlchemy URL, e.g. postgresql+psycopg2://user:pass@host/db?sslmode=require
    database_url: str = ""
    db_echo: bool = False  # log SQL statements
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True

    # --- Weather (OpenWeatherMap) ---
    # The API key stays server-side ONLY. Set it in Server/.env, never in the frontend.
    openweather_api_key: str = ""
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_units: str = "metric"  # metric -> °C, m/s (wind converted to km/h)
    weather_cache_ttl_seconds: int = 300  # cache upstream responses to respect rate limits
    weather_timeout_seconds: float = 10.0
    weather_default_district: str = "Aizawl"

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _assemble_cors_origins(cls, value: object) -> object:
        """Allow a comma-separated string (from .env) or a real list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
