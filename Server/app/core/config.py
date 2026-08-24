"""Application configuration loaded from environment variables / `.env`.

Uses pydantic-settings so configuration is validated and typed. Access the
singleton via :func:`get_settings` (cached) so the `.env` file is parsed once.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    backend_cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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
