"""Shared enumerations used across schemas and services."""

from enum import Enum


class RiskStatus(str, Enum):
    """Landslide risk severity band.

    Thresholds (see :func:`app.services.risk.band_for_score`):
        0–20 LOW · 20–40 MODERATE · 40–70 HIGH · 70–100 CRITICAL
    """

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeltaDir(str, Enum):
    """Direction of a KPI change indicator."""

    UP = "up"
    DOWN = "down"
    FLAT = "flat"


# ---------------------------------------------------------------------------
# Persistence vocabularies (used by ORM models + seed data). Values are the
# exact strings the API contract exposes, so responses need no remapping.
# ---------------------------------------------------------------------------


class UserRole(str, Enum):
    """Platform roles."""

    ADMIN = "admin"
    OFFICER = "officer"
    CITIZEN = "citizen"


class IncidentType(str, Enum):
    """Geo-tagged incident categories (matches the report form options)."""

    LANDSLIDE = "Landslide"
    ROAD_BLOCKAGE = "Road Blockage"
    SOIL_CRACK = "Soil Crack"
    SLOPE_MOVEMENT = "Slope Movement"
    FLOODING = "Flooding"


class IncidentSource(str, Enum):
    """Who reported an incident."""

    CITIZEN = "Citizen"
    FIELD_OFFICER = "Field Officer"


class IncidentStatus(str, Enum):
    """Verification lifecycle for a reported incident."""

    PENDING = "Pending"
    VERIFIED = "Verified"
    PENDING_VERIFICATION = "Pending Verification"


class RoadStatus(str, Enum):
    """Road connectivity status."""

    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    HIGH_RISK = "HIGH RISK"


class NotificationCategory(str, Enum):
    """Notification source category."""

    ALERT = "alert"
    INCIDENT = "incident"
    SYSTEM = "system"

