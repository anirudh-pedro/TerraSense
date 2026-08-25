"""AI risk prediction route — GET /api/ai/prediction."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_optional_db
from app.models.prediction import AiPredictionResponse
from app.services import prediction_service
from app.services.prediction_service import PredictionUnavailable

router = APIRouter(tags=["AI Prediction"])
logger = logging.getLogger(__name__)


@router.get(
    "/ai/prediction",
    response_model=AiPredictionResponse,
    summary="AI landslide risk prediction (gauge, factors, 24h trend)",
)
def get_ai_prediction(
    zone_id: Annotated[Optional[str], Query(alias="zoneId", description="Filter to one zone by id.")] = None,
    district: Annotated[Optional[str], Query(description="Filter to one zone by district name.")] = None,
    db: Annotated[Optional[Session], Depends(get_optional_db)] = None,
) -> AiPredictionResponse:
    """Score landslide risk with Model 2 (XGBoost + rule fusion + SHAP).

    Features are assembled from Neon where available; signals not yet wired use
    honest, internally-logged fallbacks (no fabricated sensor/satellite data).
    Defaults to the highest-risk zone when no filter is given.
    """
    try:
        return prediction_service.get_prediction(db, zone_id=zone_id, district=district)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PredictionUnavailable as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
