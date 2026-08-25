"""Seed / demo data for TerraSense NER.

Populates every table with realistic NER data aligned to the API contracts.
Idempotent: skips if data already exists (use ``--reset`` to wipe and reseed).

Usage:
    python -m app.db.seed            # seed if empty
    python -m app.db.seed --reset    # truncate all tables, then seed
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, datetime, timedelta, timezone

from geoalchemy2.elements import WKTElement
from sqlalchemy import text

from app.core.logging import configure_logging
from app.db import models as m
from app.db.base import Base
from app.db.session import get_engine, get_sessionmaker
from app.models.enums import (
    IncidentSource,
    IncidentStatus,
    IncidentType,
    NotificationCategory,
    RoadStatus,
    UserRole,
)
from app.services.risk import band_for_score

logger = logging.getLogger("terrasense.seed")


def _pt(lat: float, lng: float) -> WKTElement:
    """PostGIS point from lat/lng (note WKT order is lng lat = x y)."""
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


def _ago(minutes: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


# District name -> (state, lat, lng, population)
DISTRICTS = [
    ("Aizawl", "Mizoram", 23.7271, 92.7176, 400309),
    ("Champhai", "Mizoram", 23.4739, 93.3295, 125745),
    ("Kohima", "Nagaland", 25.6751, 94.1086, 267988),
    ("East Khasi Hills", "Meghalaya", 25.5788, 91.8933, 825922),
    ("Papum Pare", "Arunachal Pradesh", 27.0844, 93.6053, 176385),
    ("Gangtok", "Sikkim", 27.3389, 88.6065, 100286),
    ("Imphal East", "Manipur", 24.8170, 93.9368, 456113),
    ("Kamrup Metro", "Assam", 26.1445, 91.7362, 1253938),
    ("West Tripura", "Tripura", 23.8315, 91.2868, 918000),
]

# code, district, radius_m, score, rainfall, soil, slope, elev, window, pop_exposed
RISK_ZONES = [
    ("zone-aizawl", "Aizawl", 9000, 87, 182, 89, 38, 1240, "Next 6–12 hours", 4820),
    ("zone-champhai", "Champhai", 7000, 74, 141, 81, 34, 1310, "Next 12–24 hours", 2140),
    ("zone-kohima", "Kohima", 8000, 68, 118, 76, 31, 1444, "Next 24 hours", 3110),
    ("zone-shillong", "East Khasi Hills", 8500, 58, 96, 72, 27, 1496, "Next 24–36 hours", 5200),
    ("zone-itanagar", "Papum Pare", 9500, 63, 108, 74, 33, 620, "Next 24 hours", 2760),
    ("zone-gangtok", "Gangtok", 7500, 79, 156, 85, 41, 1650, "Next 6–12 hours", 3980),
    ("zone-imphal", "Imphal East", 7000, 34, 52, 58, 19, 786, "Next 48 hours", 1240),
    ("zone-guwahati", "Kamrup Metro", 9000, 41, 68, 64, 15, 55, "Next 36 hours", 6100),
    ("zone-agartala", "West Tripura", 7000, 18, 24, 44, 9, 22, "Stable", 320),
]

ALERTS = [
    ("alert-1", "Aizawl", 91, 12, "Imminent slope failure risk. Evacuation warning recommended for low-lying settlements."),
    ("alert-2", "Champhai", 74, 28, "Saturated soil and continued rainfall. Restrict movement on hill roads."),
    ("alert-3", "Kohima", 68, 41, "Elevated slope instability. Field inspection advised."),
    ("alert-4", "Gangtok", 82, 54, "Heavy rainfall over fragile terrain. Pre-position response teams."),
    ("alert-5", "East Khasi Hills", 57, 60, "Rising soil moisture near NH corridor. Monitor closely."),
]

# code, name, district, status, band, note, lat, lng
ROADS = [
    ("road-1", "NH-6", "Aizawl", RoadStatus.BLOCKED, 90, "Debris slide near km 42", 23.70, 92.90),
    ("road-2", "Aizawl–Champhai Road", "Champhai", RoadStatus.HIGH_RISK, 55, "Cracks on carriageway", 23.60, 93.00),
    ("road-3", "NH-10", "Gangtok", RoadStatus.RESTRICTED, 30, "Single-lane movement", 27.30, 88.50),
    ("road-4", "NH-2 (Kohima Bypass)", "Kohima", RoadStatus.HIGH_RISK, 55, "Slope monitoring active", 25.66, 94.10),
    ("road-5", "Shillong–Jowai Road", "East Khasi Hills", RoadStatus.RESTRICTED, 30, "Water logging", 25.50, 92.00),
]

# code, name, type, district, lat, lng
INFRASTRUCTURE = [
    ("infra-1", "Aizawl Civil Hospital", "Hospital", "Aizawl", 23.728, 92.719),
    ("infra-2", "Gangtok Relief Depot", "Relief Depot", "Gangtok", 27.335, 88.610),
    ("infra-3", "Kohima Emergency Ops", "Command", "Kohima", 25.676, 94.107),
]

# rank, district, risk, pop, road_status, action
PRIORITIES = [
    (1, "Aizawl", 94, 4820, "Blocked", "Deploy response team and issue evacuation warning."),
    (2, "Champhai", 78, 2140, "Restricted", "Deploy field inspection team."),
    (3, "Gangtok", 79, 3980, "Restricted", "Pre-position relief supplies and alert local authorities."),
    (4, "Kohima", 68, 3110, "Open", "Maintain monitoring and ready standby teams."),
]

# code, title, minutes_ago, band_score, category
NOTIFICATIONS = [
    ("n1", "Critical alert issued — Aizawl", 12, 95, NotificationCategory.ALERT),
    ("n2", "NH-6 reported blocked", 24, 90, NotificationCategory.INCIDENT),
    ("n3", "New citizen report — Champhai", 16, 55, NotificationCategory.INCIDENT),
    ("n4", "Rainfall threshold exceeded — Gangtok", 38, 55, NotificationCategory.SYSTEM),
]

# code, district, type, severity_score, source, status, minutes_ago
INCIDENTS = [
    ("rep-1", "Aizawl", IncidentType.SOIL_CRACK, 55, IncidentSource.FIELD_OFFICER, IncidentStatus.VERIFIED, 8),
    ("rep-2", "Champhai", IncidentType.ROAD_BLOCKAGE, 90, IncidentSource.CITIZEN, IncidentStatus.PENDING, 16),
    ("rep-3", "Kohima", IncidentType.SLOPE_MOVEMENT, 55, IncidentSource.FIELD_OFFICER, IncidentStatus.VERIFIED, 31),
    ("rep-4", "Gangtok", IncidentType.LANDSLIDE, 90, IncidentSource.CITIZEN, IncidentStatus.PENDING, 47),
    ("rep-5", "East Khasi Hills", IncidentType.FLOODING, 30, IncidentSource.FIELD_OFFICER, IncidentStatus.VERIFIED, 60),
    ("rep-6", "Papum Pare", IncidentType.ROAD_BLOCKAGE, 55, IncidentSource.CITIZEN, IncidentStatus.PENDING, 75),
]

AI_FACTORS = [
    {"name": "Heavy Rainfall", "level": "High", "weight": 0.90},
    {"name": "Soil Moisture", "level": "Very High", "weight": 0.95},
    {"name": "Slope", "level": "38°", "weight": 0.82},
    {"name": "Historical Activity", "level": "High", "weight": 0.78},
    {"name": "Terrain Stability", "level": "Low", "weight": 0.85},
]
AI_TREND = [
    {"time": f"{h:02d}:00", "risk": r}
    for h, r in zip(range(0, 24, 2), [41, 44, 48, 52, 57, 61, 66, 70, 74, 79, 83, 87])
]

WEATHER_FORECAST = [
    {"time": t, "rain": r}
    for t, r in zip(
        ["Now", "+1h", "+2h", "+3h", "+4h", "+5h", "+6h", "+7h", "+8h", "+9h", "+10h", "+11h"],
        [42, 46, 51, 48, 55, 59, 53, 44, 38, 29, 21, 16],
    )
]

# district, occurred_on, severity_score, fatalities, description
LANDSLIDE_HISTORY = [
    ("Aizawl", date(2017, 5, 11), 90, 7, "Major slope failure after prolonged monsoon rainfall."),
    ("Gangtok", date(2019, 6, 24), 80, 3, "Debris flow blocked NH-10 for several days."),
    ("Kohima", date(2021, 7, 2), 60, 0, "Road embankment slip during heavy rain."),
    ("East Khasi Hills", date(2022, 6, 15), 55, 1, "Hillside collapse near quarry site."),
]

_ALL_TABLES_REVERSE = [
    m.Notification, m.EmergencyPriority, m.Infrastructure, m.Road, m.Incident,
    m.Alert, m.AiPrediction, m.LandslideHistory, m.SoilMoisture, m.TerrainData,
    m.WeatherData, m.RiskZone, m.District, m.User,
]


def reset(session) -> None:
    """Truncate all domain tables (keeps schema + alembic_version)."""
    table_names = ", ".join(model.__tablename__ for model in _ALL_TABLES_REVERSE)
    session.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    session.commit()
    logger.info("Truncated all domain tables")


def seed(session) -> None:
    # --- Users ---
    session.add_all([
        m.User(email="admin@mdoner.gov.in", full_name="Administrator", role=UserRole.ADMIN, is_active=True),
        m.User(email="officer@mdoner.gov.in", full_name="Field Officer", role=UserRole.OFFICER, is_active=True),
        m.User(email="citizen@example.com", full_name="Community Reporter", role=UserRole.CITIZEN, is_active=True),
    ])
    session.flush()
    officer = session.query(m.User).filter_by(role=UserRole.OFFICER).first()
    citizen = session.query(m.User).filter_by(role=UserRole.CITIZEN).first()

    # --- Districts ---
    districts: dict[str, m.District] = {}
    for name, state, lat, lng, pop in DISTRICTS:
        d = m.District(name=name, state=state, code=name.lower().replace(" ", "-"),
                       centroid=_pt(lat, lng), population=pop)
        districts[name] = d
        session.add(d)
    session.flush()

    # --- Risk zones (status derived from score) ---
    zones: dict[str, m.RiskZone] = {}
    for code, dname, radius, score, rain, soil, slope, elev, window, pop in RISK_ZONES:
        d = districts[dname]
        lat, lng = next((la, ln) for n, _, la, ln, _ in DISTRICTS if n == dname)
        z = m.RiskZone(
            code=code, district_id=d.id, name=dname, center=_pt(lat, lng),
            radius_m=radius, risk_score=score, status=band_for_score(score),
            rainfall_mm=rain, soil_moisture_pct=soil, slope_deg=slope,
            elevation_m=elev, prediction_window=window, population_exposed=pop,
        )
        zones[dname] = z
        session.add(z)
    session.flush()

    # --- Weather (current + 12h forecast) for a few districts ---
    session.add_all([
        m.WeatherData(district_id=districts["Aizawl"].id, location=_pt(23.7271, 92.7176),
                      temperature_c=24, humidity_pct=91, rainfall_mm_hr=42, wind_kmh=18,
                      warning="Heavy rainfall expected for the next 8 hours", forecast=WEATHER_FORECAST),
        m.WeatherData(district_id=districts["Gangtok"].id, location=_pt(27.3389, 88.6065),
                      temperature_c=21, humidity_pct=88, rainfall_mm_hr=36, wind_kmh=14,
                      warning="Sustained rainfall over fragile terrain", forecast=WEATHER_FORECAST),
    ])

    # --- Terrain + soil moisture ---
    session.add_all([
        m.TerrainData(district_id=districts["Aizawl"].id, risk_zone_id=zones["Aizawl"].id,
                      location=_pt(23.7271, 92.7176), slope_deg=38, elevation_m=1240,
                      aspect_deg=210, stability_index=0.28, source="DEM/SRTM"),
        m.TerrainData(district_id=districts["Gangtok"].id, risk_zone_id=zones["Gangtok"].id,
                      location=_pt(27.3389, 88.6065), slope_deg=41, elevation_m=1650,
                      aspect_deg=185, stability_index=0.24, source="DEM/SRTM"),
        m.TerrainData(district_id=districts["Kohima"].id, risk_zone_id=zones["Kohima"].id,
                      location=_pt(25.6751, 94.1086), slope_deg=31, elevation_m=1444,
                      aspect_deg=160, stability_index=0.41, source="DEM/SRTM"),
    ])
    session.add_all([
        m.SoilMoisture(district_id=districts["Aizawl"].id, location=_pt(23.7271, 92.7176),
                       moisture_pct=89, depth_cm=30, source="ISRO/Sensor"),
        m.SoilMoisture(district_id=districts["Champhai"].id, location=_pt(23.4739, 93.3295),
                       moisture_pct=81, depth_cm=30, source="ISRO/Sensor"),
        m.SoilMoisture(district_id=districts["Gangtok"].id, location=_pt(27.3389, 88.6065),
                       moisture_pct=85, depth_cm=30, source="ISRO/Sensor"),
    ])

    # --- Landslide history ---
    for dname, occurred, sev, fatalities, desc in LANDSLIDE_HISTORY:
        d = districts[dname]
        lat, lng = next((la, ln) for n, _, la, ln, _ in DISTRICTS if n == dname)
        session.add(m.LandslideHistory(district_id=d.id, location=_pt(lat, lng), occurred_on=occurred,
                                        severity=band_for_score(sev), fatalities=fatalities,
                                        description=desc, source="Historical records"))

    # --- AI prediction (Aizawl) ---
    session.add(m.AiPrediction(
        risk_zone_id=zones["Aizawl"].id, district_id=districts["Aizawl"].id,
        risk_score=87, status=band_for_score(87),
        summary="High probability of slope failure within the next 6–12 hours.",
        prediction_window="Next 6–12 hours", factors=AI_FACTORS, trend=AI_TREND,
        model_version="v3.2",
    ))

    # --- Alerts ---
    for code, dname, prob, mins, message in ALERTS:
        session.add(m.Alert(
            code=code, district_id=districts[dname].id, risk_zone_id=zones[dname].id,
            probability=prob, status=band_for_score(prob), message=message,
            issued_at=_ago(mins), resolved=False,
        ))

    # --- Roads ---
    for code, name, dname, status, band_score, note, lat, lng in ROADS:
        session.add(m.Road(
            code=code, name=name, district_id=districts[dname].id, status=status,
            band=band_for_score(band_score), note=note, location=_pt(lat, lng),
        ))

    # --- Infrastructure ---
    for code, name, itype, dname, lat, lng in INFRASTRUCTURE:
        session.add(m.Infrastructure(code=code, name=name, type=itype,
                                     district_id=districts[dname].id, location=_pt(lat, lng)))

    # --- Emergency priorities ---
    for rank, dname, risk, pop, road_status, action in PRIORITIES:
        session.add(m.EmergencyPriority(
            rank=rank, district_id=districts[dname].id, risk_zone_id=zones[dname].id,
            risk=risk, population_exposed=pop, road_status=road_status, action=action,
            status=band_for_score(risk),
        ))

    # --- Notifications ---
    for code, title, mins, band_score, category in NOTIFICATIONS:
        n = m.Notification(code=code, title=title, band=band_for_score(band_score), category=category)
        n.created_at = _ago(mins)
        session.add(n)

    # --- Incidents (geo-tagged) ---
    for code, dname, itype, sev, source, status, mins in INCIDENTS:
        d = districts[dname]
        lat, lng = next((la, ln) for n, _, la, ln, _ in DISTRICTS if n == dname)
        reporter = officer if source == IncidentSource.FIELD_OFFICER else citizen
        session.add(m.Incident(
            code=code, district_id=d.id, reported_by_id=reporter.id if reporter else None,
            incident_type=itype, severity=band_for_score(sev), source=source,
            location=_pt(lat, lng), location_text=dname,
            description=f"{itype.value} reported near {dname}.",
            status=status, reported_at=_ago(mins),
        ))

    session.commit()
    logger.info("Seed complete")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Seed TerraSense demo data")
    parser.add_argument("--reset", action="store_true", help="truncate all tables before seeding")
    args = parser.parse_args()

    # Ensure schema exists (safe no-op if migrations already applied).
    Base.metadata.create_all(bind=get_engine())

    session = get_sessionmaker()()
    try:
        if args.reset:
            reset(session)
        elif session.query(m.District).count() > 0:
            logger.info("Data already present — skipping. Use --reset to reseed.")
            return
        seed(session)
        counts = {model.__tablename__: session.query(model).count() for model in _ALL_TABLES_REVERSE}
        logger.info("Row counts: %s", counts)
    finally:
        session.close()


if __name__ == "__main__":
    main()
