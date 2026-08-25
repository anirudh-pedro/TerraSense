"""SQLAlchemy ORM models for TerraSense NER (Phase 1).

Design notes
------------
* Coordinates & GIS entities use PostGIS geometry (SRID 4326 / WGS84) via
  GeoAlchemy2 — points for locations, linestrings for roads, polygons for
  district boundaries.
* Enum columns store the exact API-contract string values (via ``values_callable``)
  so responses require no remapping.
* Every geometry column gets a GIST spatial index (``spatial_index=True``).
* Public string identifiers from the API (e.g. ``zone-aizawl``, ``alert-1``)
  are stored in a ``code`` slug column; integer surrogate keys are used for FKs.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import (
    IncidentSource,
    IncidentStatus,
    IncidentType,
    NotificationCategory,
    RiskStatus,
    RoadStatus,
    UserRole,
)


def _enum(py_enum, name: str) -> SAEnum:
    """Build a native PostgreSQL enum that stores the enum *values*."""
    return SAEnum(
        py_enum,
        name=name,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
        native_enum=True,
    )


# Shared enum type instances — reused across columns/tables so PostgreSQL only
# creates each enum type once (important for create_all and the migration).
RISK_STATUS = _enum(RiskStatus, "risk_status")
USER_ROLE = _enum(UserRole, "user_role")
INCIDENT_TYPE = _enum(IncidentType, "incident_type")
INCIDENT_SOURCE = _enum(IncidentSource, "incident_source")
INCIDENT_STATUS = _enum(IncidentStatus, "incident_status")
ROAD_STATUS = _enum(RoadStatus, "road_status")
NOTIFICATION_CATEGORY = _enum(NotificationCategory, "notification_category")


# Reusable geometry column factories (SRID 4326 = WGS84 lat/lng).
def _point(nullable: bool = True):
    return mapped_column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=nullable)


def _linestring(nullable: bool = True):
    return mapped_column(Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True), nullable=nullable)


def _multipolygon(nullable: bool = True):
    return mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True), nullable=nullable)


# ============================================================ users =========
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(USER_ROLE, nullable=False, default=UserRole.CITIZEN)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    incidents: Mapped[list["Incident"]] = relationship(back_populates="reported_by")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")


# ======================================================== districts =========
class District(Base, TimestampMixin):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("name", "state", name="uq_districts_name_state"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(40), unique=True, nullable=True)
    centroid = _point(nullable=True)
    boundary = _multipolygon(nullable=True)
    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    area_sq_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    risk_zones: Mapped[list["RiskZone"]] = relationship(back_populates="district")
    weather_data: Mapped[list["WeatherData"]] = relationship(back_populates="district")
    terrain_data: Mapped[list["TerrainData"]] = relationship(back_populates="district")
    soil_moisture: Mapped[list["SoilMoisture"]] = relationship(back_populates="district")
    landslide_history: Mapped[list["LandslideHistory"]] = relationship(back_populates="district")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="district")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="district")
    roads: Mapped[list["Road"]] = relationship(back_populates="district")
    infrastructure: Mapped[list["Infrastructure"]] = relationship(back_populates="district")
    emergency_priorities: Mapped[list["EmergencyPriority"]] = relationship(back_populates="district")


# ======================================================== risk_zones ========
class RiskZone(Base, TimestampMixin):
    __tablename__ = "risk_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    center = _point(nullable=False)
    radius_m: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False, index=True)
    # Current environmental snapshot (denormalized to match the /risk-zones contract).
    rainfall_mm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    soil_moisture_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slope_deg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    elevation_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prediction_window: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    population_exposed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    district: Mapped[Optional["District"]] = relationship(back_populates="risk_zones")
    ai_predictions: Mapped[list["AiPrediction"]] = relationship(back_populates="risk_zone")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="risk_zone")
    emergency_priorities: Mapped[list["EmergencyPriority"]] = relationship(back_populates="risk_zone")


# ====================================================== weather_data ========
class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location = _point(nullable=True)
    temperature_c: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    humidity_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rainfall_mm_hr: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    wind_kmh: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    warning: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    forecast: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # [{time, rain}, ...]
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    district: Mapped["District"] = relationship(back_populates="weather_data")


# ====================================================== terrain_data ========
class TerrainData(Base):
    __tablename__ = "terrain_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_zone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("risk_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location = _point(nullable=True)
    slope_deg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    elevation_m: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    aspect_deg: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    stability_index: Mapped[Optional[float]] = mapped_column(Numeric(4, 3), nullable=True)  # 0..1
    source: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    district: Mapped["District"] = relationship(back_populates="terrain_data")


# ====================================================== soil_moisture =======
class SoilMoisture(Base):
    __tablename__ = "soil_moisture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location = _point(nullable=True)
    moisture_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    depth_cm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    district: Mapped["District"] = relationship(back_populates="soil_moisture")


# =================================================== landslide_history ======
class LandslideHistory(Base):
    __tablename__ = "landslide_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location = _point(nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    severity: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False)
    fatalities: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    district: Mapped[Optional["District"]] = relationship(back_populates="landslide_history")


# ===================================================== ai_predictions =======
class AiPrediction(Base):
    __tablename__ = "ai_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    risk_zone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("risk_zones.id", ondelete="CASCADE"), nullable=True, index=True
    )
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prediction_window: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    factors: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # [{name, level, weight}]
    trend: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # [{time, risk}]
    model_version: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    risk_zone: Mapped[Optional["RiskZone"]] = relationship(back_populates="ai_predictions")


# =========================================================== alerts =========
class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(60), unique=True, nullable=True)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    risk_zone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("risk_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    probability: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), index=True)

    district: Mapped[Optional["District"]] = relationship(back_populates="alerts")
    risk_zone: Mapped[Optional["RiskZone"]] = relationship(back_populates="alerts")


# ========================================================= incidents ========
class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(60), unique=True, nullable=True)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reported_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_type: Mapped[IncidentType] = mapped_column(INCIDENT_TYPE, nullable=False)
    severity: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False, index=True)
    source: Mapped[IncidentSource] = mapped_column(INCIDENT_SOURCE, nullable=False)
    location = _point(nullable=True)
    location_text: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        INCIDENT_STATUS, nullable=False, default=IncidentStatus.PENDING, index=True
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    district: Mapped[Optional["District"]] = relationship(back_populates="incidents")
    reported_by: Mapped[Optional["User"]] = relationship(back_populates="incidents")


# ============================================================ roads =========
class Road(Base, TimestampMixin):
    __tablename__ = "roads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(60), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[RoadStatus] = mapped_column(ROAD_STATUS, nullable=False, index=True)
    band: Mapped[Optional[RiskStatus]] = mapped_column(RISK_STATUS, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path = _linestring(nullable=True)
    location = _point(nullable=True)  # marker coordinates for "View on Map"

    district: Mapped[Optional["District"]] = relationship(back_populates="roads")


# ======================================================= infrastructure =====
class Infrastructure(Base, TimestampMixin):
    __tablename__ = "infrastructure"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(60), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    type: Mapped[str] = mapped_column(String(60), nullable=False)  # Hospital / Relief Depot / Command ...
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location = _point(nullable=False)

    district: Mapped[Optional["District"]] = relationship(back_populates="infrastructure")


# =================================================== emergency_priorities ===
class EmergencyPriority(Base, TimestampMixin):
    __tablename__ = "emergency_priorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    district_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    risk_zone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("risk_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    risk: Mapped[int] = mapped_column(Integer, nullable=False)
    population_exposed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    road_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[RiskStatus] = mapped_column(RISK_STATUS, nullable=False)

    district: Mapped[Optional["District"]] = relationship(back_populates="emergency_priorities")
    risk_zone: Mapped[Optional["RiskZone"]] = relationship(back_populates="emergency_priorities")


# ======================================================= notifications ======
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    band: Mapped[Optional[RiskStatus]] = mapped_column(RISK_STATUS, nullable=True)
    category: Mapped[Optional[NotificationCategory]] = mapped_column(
        NOTIFICATION_CATEGORY, nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="notifications")


