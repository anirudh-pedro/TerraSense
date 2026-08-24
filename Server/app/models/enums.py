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
