"""Weather service — orchestrates the external-data ingestion pipeline.

Flow:  OpenWeatherMap (provider) -> normalize -> persist to Neon -> API response

Read-through caching / controlled polling:
    A district's latest observation is reused while it is within
    ``WEATHER_CACHE_TTL_SECONDS`` (no upstream call). When stale/missing, the
    provider is queried, the result is persisted, and then returned.

Resilience:
    If the provider fails, the most recent stored observation (even if stale)
    is served as a fallback. The service degrades gracefully when the database
    is unavailable (live fetch, no persistence).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import WeatherData
from app.db.repositories import weather_repo
from app.integrations.base import ProviderError
from app.integrations.openweather import NormalizedWeather, OpenWeatherProvider
from app.models.weather import WeatherForecastPoint, WeatherResponse
from app.services.locations import resolve_location

logger = logging.getLogger(__name__)

# Single provider instance (stateless aside from config).
_provider = OpenWeatherProvider()


class WeatherUnavailable(Exception):
    """Raised when weather cannot be produced (upstream/config failure)."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _forecast_points(raw: Optional[list]) -> list[WeatherForecastPoint]:
    return [WeatherForecastPoint(time=p["time"], rain=int(p["rain"])) for p in (raw or [])]


def _response_from_row(name: str, row: WeatherData) -> WeatherResponse:
    return WeatherResponse(
        district=name,
        temperature=round(float(row.temperature_c or 0)),
        humidity=int(row.humidity_pct or 0),
        rainfall=round(float(row.rainfall_mm_hr or 0)),
        wind=round(float(row.wind_kmh or 0)),
        warning=row.warning,
        forecast=_forecast_points(row.forecast),
    )


def _response_from_normalized(name: str, data: NormalizedWeather) -> WeatherResponse:
    return WeatherResponse(
        district=name,
        temperature=round(data.temperature_c),
        humidity=int(data.humidity_pct),
        rainfall=round(data.rainfall_mm_hr),
        wind=round(data.wind_kmh),
        warning=data.warning,
        forecast=_forecast_points(data.forecast),
    )


def get_weather(db: Optional[Session], district: Optional[str] = None) -> WeatherResponse:
    """Return live weather for a district (contract: WeatherResponse)."""
    settings = get_settings()
    location = resolve_location(db, district)
    can_persist = db is not None and location.district_id is not None

    # 1) Read-through cache: serve a recent stored observation if fresh.
    if can_persist:
        fresh = weather_repo.get_fresh(db, location.district_id, settings.weather_cache_ttl_seconds)
        if fresh is not None:
            logger.debug("Weather cache hit (DB) for %s", location.name)
            return _response_from_row(location.name, fresh)

    # 2) Fetch from the external provider.
    try:
        normalized = _provider.fetch(location.latitude, location.longitude)
    except ProviderError as exc:
        # 3) Fallback to the last known observation if the provider is down.
        if can_persist:
            last = weather_repo.get_latest(db, location.district_id)
            if last is not None:
                logger.warning("Provider failed for %s; serving stale DB observation.", location.name)
                return _response_from_row(location.name, last)
        raise WeatherUnavailable(exc.message, exc.status_code) from exc

    # 4) Persist the fresh observation (best-effort; never fail the request on write).
    if can_persist:
        try:
            weather_repo.save(db, location.district_id, normalized)
            logger.info("Persisted weather for %s (district_id=%s)", location.name, location.district_id)
        except Exception:
            logger.exception("Failed to persist weather for %s", location.name)
            db.rollback()

    return _response_from_normalized(location.name, normalized)
