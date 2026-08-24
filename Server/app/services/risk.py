"""Risk scoring helpers.

Single source of truth for turning a numeric risk score into a severity band.
Keeping this here (not in routes or data) means the ML layer can later feed raw
scores and the API keeps deriving status identically.
"""

from app.models.enums import RiskStatus

# Inclusive-lower bounds. Thresholds: 0–20 LOW, 20–40 MODERATE, 40–70 HIGH, 70–100 CRITICAL.
_CRITICAL_MIN = 70
_HIGH_MIN = 40
_MODERATE_MIN = 20


def band_for_score(score: float) -> RiskStatus:
    """Map a 0–100 risk score to its :class:`RiskStatus` band."""
    if score >= _CRITICAL_MIN:
        return RiskStatus.CRITICAL
    if score >= _HIGH_MIN:
        return RiskStatus.HIGH
    if score >= _MODERATE_MIN:
        return RiskStatus.MODERATE
    return RiskStatus.LOW
