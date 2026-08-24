"""KPI summary service."""

import logging

from app.models.kpi import KpiSummary
from app.services import mock_data

logger = logging.getLogger(__name__)


def get_kpi_summary() -> KpiSummary:
    """Return the four Risk Overview KPI cards."""
    logger.debug("Fetching KPI summary")
    return KpiSummary(**mock_data.KPI_SUMMARY)
