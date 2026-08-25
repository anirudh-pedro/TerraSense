"""OpenWeatherMap provider.

Fetches current conditions + short-term forecast and normalizes them into a
source-agnostic :class:`NormalizedWeather` payload. The API key is read from
server-side settings and never leaves the backend.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.integrations.base import DataSource, ExternalDataProvider, ProviderError

logger = logging.getLogger(__name__)

# NER uses IST (UTC+5:30) — used only for human-readable forecast time labels.
_IST = timezone(timedelta(hours=5, minutes=30))

# OpenWeatherMap rainfall intensity bands (mm/hr).
_HEAVY_RAIN = 7.6
_MODERATE_RAIN = 2.5

# Number of 3-hourly forecast buckets to keep (~21h) beyond the leading "Now".
_FORECAST_POINTS = 7


@dataclass
class NormalizedWeather:
    """Source-agnostic weather payload persisted + returned by the API."""

    latitude: float
    longitude: float
    temperature_c: float
    humidity_pct: int
    rainfall_mm_hr: float
    wind_kmh: float
    warning: str | None
    forecast: list[dict]  # [{"time": "15:00", "rain": 4}, ...]
    observed_at: datetime


class OpenWeatherProvider(ExternalDataProvider):
    """Weather source backed by the OpenWeatherMap 2.5 API."""

    name = "openweathermap"
    source = DataSource.WEATHER

    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(timeout=settings.weather_timeout_seconds)
        self._api_key = settings.openweather_api_key
        self._base_url = settings.openweather_base_url
        self._units = settings.weather_units

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def fetch(self, latitude: float, longitude: float) -> NormalizedWeather:
        """Fetch + normalize current conditions and forecast for a coordinate."""
        if not self.configured:
            raise ProviderError("Weather service is not configured on the server.", 503)

        params = {"lat": latitude, "lon": longitude, "appid": self._api_key, "units": self._units}
        current = self._get_json(f"{self._base_url}/weather", params=params)
        forecast = self._get_json(f"{self._base_url}/forecast", params=params)
        return self._normalize(latitude, longitude, current, forecast)

    @staticmethod
    def _classify_warning(peak_mm_hr: float) -> str | None:
        if peak_mm_hr >= _HEAVY_RAIN:
            return "Heavy rainfall expected over the next several hours"
        if peak_mm_hr >= _MODERATE_RAIN:
            return "Moderate rainfall expected in the coming hours"
        return None

    def _normalize(self, latitude: float, longitude: float, current: dict, forecast: dict) -> NormalizedWeather:
        main = current.get("main", {})
        wind = current.get("wind", {})
        current_rain = float(current.get("rain", {}).get("1h", 0.0))

        points: list[dict] = [{"time": "Now", "rain": round(current_rain)}]
        rains: list[float] = [current_rain]

        for entry in forecast.get("list", [])[:_FORECAST_POINTS]:
            rain_3h = float(entry.get("rain", {}).get("3h", 0.0))
            rain_mm_hr = rain_3h / 3.0  # 3-hour accumulation -> average intensity
            rains.append(rain_mm_hr)
            label = datetime.fromtimestamp(entry["dt"], tz=timezone.utc).astimezone(_IST).strftime("%H:%M")
            points.append({"time": label, "rain": round(rain_mm_hr)})

        observed_ts = current.get("dt")
        observed_at = (
            datetime.fromtimestamp(observed_ts, tz=timezone.utc)
            if observed_ts
            else datetime.now(timezone.utc)
        )

        return NormalizedWeather(
            latitude=latitude,
            longitude=longitude,
            temperature_c=float(main.get("temp", 0.0)),
            humidity_pct=int(round(float(main.get("humidity", 0.0)))),
            rainfall_mm_hr=current_rain,
            wind_kmh=float(wind.get("speed", 0.0)) * 3.6,  # m/s -> km/h
            warning=self._classify_warning(max(rains) if rains else 0.0),
            forecast=points,
            observed_at=observed_at,
        )
