"""AI Risk Prediction orchestrator (Model 2).

Assembles the model's feature snapshot per zone from data available in Neon
(risk-zone snapshot + environmental columns), applies honest fallbacks for
signals not yet wired (Model 1 susceptibility, multi-window rainfall, soil-
moisture trend, NDVI, soil type, disturbance), and delegates scoring to the
vendored `app.ml.ai_prediction_service`.

Principles:
- No fabricated sensor/satellite values. Unavailable features are passed as
  ``None`` so the model degrades gracefully; each fallback is logged.
- `susceptibility_score` (normally Model 1's output) temporarily uses the stored
  risk score as a proxy, clearly flagged, until Model 1 is integrated.
- The heavy ML deps + model artifact are imported lazily so the rest of the API
  stays up even if they're missing (returns a clean 503 instead).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import RiskZone
from app.services import mock_data

logger = logging.getLogger(__name__)

# Features with no wired data source yet — passed as None (never fabricated).
_UNAVAILABLE_FEATURES = [
    "rain_3d", "rain_7d", "rain_15d", "rain_30d", "api_index",
    "seasonal_cum_rain", "seasonal_rain_anomaly", "soil_moisture_trend",
    "ndvi", "ndvi_change_30d", "soil_type", "disturbance_index",
]


class PredictionUnavailable(Exception):
    """Raised when a prediction cannot be produced (deps/artifact/scoring)."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _features_from_values(
    *,
    risk_score: Optional[int],
    slope_deg: Optional[float],
    soil_moisture_pct: Optional[float],
    rainfall_mm: Optional[float],
) -> dict:
    """Map available zone data to the model's 15-feature schema.

    Only real, available values are populated; everything else is ``None`` so
    the model's graceful-degradation path handles it.
    """
    features: dict = {}

    # susceptibility_score: Model 1 output — TEMPORARY proxy from stored score.
    if risk_score is not None:
        features["susceptibility_score"] = round(_clamp01(risk_score / 100.0), 4)
    else:
        features["susceptibility_score"] = 0.5  # neutral fallback

    # Real snapshot values from the DB where present.
    features["slope_angle_deg"] = float(slope_deg) if slope_deg is not None else None
    features["soil_moisture"] = (
        round(_clamp01(soil_moisture_pct / 100.0), 4) if soil_moisture_pct is not None else None
    )
    features["rain_1d"] = float(rainfall_mm) if rainfall_mm is not None else None

    # No data source yet — do not fabricate.
    for key in _UNAVAILABLE_FEATURES:
        features.setdefault(key, None)

    return features


def _zones_from_db(db: Session) -> list[dict]:
    rows = db.execute(select(RiskZone).options(joinedload(RiskZone.district))).scalars().all()
    zones = []
    for z in rows:
        features = _features_from_values(
            risk_score=z.risk_score,
            slope_deg=z.slope_deg,
            soil_moisture_pct=z.soil_moisture_pct,
            rainfall_mm=z.rainfall_mm,
        )
        zones.append({
            "zone_id": z.code,
            "district": z.name,
            "state": z.district.state if z.district else None,
            "features": features,
            "history": None,  # no 2-hourly logging pipeline yet -> simulated trend
        })
    return zones


def _zones_from_mock() -> list[dict]:
    zones = []
    for r in mock_data.RISK_ZONES:
        features = _features_from_values(
            risk_score=r.get("riskScore"),
            slope_deg=r.get("slope"),
            soil_moisture_pct=r.get("soilMoisture"),
            rainfall_mm=r.get("rainfall"),
        )
        zones.append({
            "zone_id": r["id"],
            "district": r["district"],
            "state": r["state"],
            "features": features,
            "history": None,
        })
    return zones


def get_prediction(
    db: Optional[Session], zone_id: Optional[str] = None, district: Optional[str] = None
) -> dict:
    """Return the AI prediction for a zone/district (or the highest-risk zone)."""
    if db is not None:
        zones = _zones_from_db(db)
        source = "neon"
        if not zones:
            zones = _zones_from_mock()
            source = "mock (empty DB)"
    else:
        zones = _zones_from_mock()
        source = "mock (no DB configured)"

    logger.info(
        "AI prediction: %d zone(s) from %s. FALLBACKS: susceptibility_score=proxy(risk_score/100, "
        "Model 1 unavailable); unavailable(None)=%s; trend=simulated (no 2-hourly history).",
        len(zones), source, ",".join(_UNAVAILABLE_FEATURES),
    )

    # Lazy import so missing ML deps/artifact don't take down the whole API.
    try:
        from app.ml import ai_prediction_service as model2
    except ImportError as exc:
        logger.exception("Prediction ML dependencies unavailable")
        raise PredictionUnavailable("Prediction model dependencies are not installed.", 503) from exc

    try:
        result = model2.get_ai_prediction(zones, zone_id=zone_id, district=district)
    except ValueError as exc:  # no matching zone for the given filter
        raise LookupError(str(exc)) from exc
    except FileNotFoundError as exc:
        logger.exception("Model artifact not found at %s", getattr(model2, "MODEL_PATH", "?"))
        raise PredictionUnavailable("Prediction model artifact not found.", 503) from exc
    except Exception as exc:  # scoring/SHAP failure
        logger.exception("AI prediction scoring failed")
        raise PredictionUnavailable("Prediction service error while scoring.", 500) from exc

    logger.info(
        "AI prediction -> zone=%s district=%s riskScore=%s status=%s trend_source=%s",
        zone_id, result.get("district"), result.get("riskScore"),
        result.get("status"), result.get("trend_source"),
    )
    return result
