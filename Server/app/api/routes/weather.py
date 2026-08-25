"""Weather routes."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_optional_db
from app.models.weather import WeatherResponse
from app.services import weather_service
from app.services.weather_service import WeatherUnavailable

router = APIRouter(tags=["Weather"])
logger = logging.getLogger(__name__)


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Live weather & rainfall forecast for a district",
)
def get_weather(
    district: Annotated[
        Optional[str],
        Query(description="NER district (or state/city). Defaults to the configured district."),
    ] = None,
    db: Annotated[Optional[Session], Depends(get_optional_db)] = None,
) -> WeatherResponse:
    """Return live conditions + rainfall forecast.

    Served through the ingestion pipeline (OpenWeatherMap -> Neon -> API) with
    read-through caching. The provider API key is used server-side only and is
    never exposed to the client.
    """
    try:
        return weather_service.get_weather(db, district)
    except WeatherUnavailable as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
