"""Region routes."""

from fastapi import APIRouter

from app.models.region import RegionMeta
from app.services import region_service

router = APIRouter(prefix="/region", tags=["Region"])


@router.get("/meta", response_model=RegionMeta, summary="Region banner + default map view")
def get_region_meta() -> RegionMeta:
    """Return region metadata used by the header and the map's initial view."""
    return region_service.get_region_meta()
