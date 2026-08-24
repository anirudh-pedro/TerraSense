"""KPI routes."""

from fastapi import APIRouter

from app.models.kpi import KpiSummary
from app.services import kpi_service

router = APIRouter(prefix="/kpis", tags=["KPIs"])


@router.get("/summary", response_model=KpiSummary, summary="Risk Overview KPI cards")
def get_kpi_summary() -> KpiSummary:
    """Return the four dashboard KPI cards (value, band, delta and trend)."""
    return kpi_service.get_kpi_summary()
