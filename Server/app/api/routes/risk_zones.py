"""Risk zone routes."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.models.risk_zone import RiskZone
from app.services import risk_zone_service

router = APIRouter(tags=["Risk Zones"])


@router.get(
    "/risk-zones",
    response_model=list[RiskZone],
    summary="AI-assessed landslide risk zones",
)
def list_risk_zones(
    state: Annotated[
        str | None,
        Query(description="Optional NER state filter (e.g. 'Mizoram'). Omit for all."),
    ] = None,
) -> list[RiskZone]:
    """Return risk zones for the GIS map. `status` is derived from `riskScore`."""
    return risk_zone_service.list_risk_zones(state=state)
