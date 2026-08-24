"""Health check route."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.common import HealthResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, summary="Backend health check")
def health() -> HealthResponse:
    """Liveness probe: confirms the API is up and reports basic metadata."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        time=datetime.now(timezone.utc).isoformat(),
    )
