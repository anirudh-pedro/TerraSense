"""Persistence for weather observations (weather_data table)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WeatherData
from app.integrations.openweather import NormalizedWeather


def get_fresh(db: Session, district_id: int, ttl_seconds: int) -> Optional[WeatherData]:
    """Return the latest observation for a district if within the TTL window."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
    stmt = (
        select(WeatherData)
        .where(WeatherData.district_id == district_id, WeatherData.observed_at >= cutoff)
        .order_by(WeatherData.observed_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def get_latest(db: Session, district_id: int) -> Optional[WeatherData]:
    """Return the most recent observation for a district regardless of age."""
    stmt = (
        select(WeatherData)
        .where(WeatherData.district_id == district_id)
        .order_by(WeatherData.observed_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def save(db: Session, district_id: int, data: NormalizedWeather) -> WeatherData:
    """Persist a normalized weather observation and return the stored row."""
    row = WeatherData(
        district_id=district_id,
        location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
        temperature_c=data.temperature_c,
        humidity_pct=data.humidity_pct,
        rainfall_mm_hr=data.rainfall_mm_hr,
        wind_kmh=data.wind_kmh,
        warning=data.warning,
        forecast=data.forecast,
        observed_at=data.observed_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
