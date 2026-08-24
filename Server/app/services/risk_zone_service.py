"""Risk zone service.

Derives the severity `status` from `riskScore` for every zone, and supports an
optional state filter to back the frontend's state/district selector.
"""

import logging

from app.models.risk_zone import RiskZone
from app.services import mock_data
from app.services.risk import band_for_score

logger = logging.getLogger(__name__)

# Sentinel value the frontend sends when no state filter is applied.
_ALL_STATES = "all ner states"


def list_risk_zones(state: str | None = None) -> list[RiskZone]:
    """Return all risk zones, optionally filtered by NER state.

    `status` is computed here from `riskScore` — never read from source data.
    """
    records = mock_data.RISK_ZONES

    if state and state.strip().lower() not in ("", _ALL_STATES):
        wanted = state.strip().lower()
        records = [r for r in records if r["state"].lower() == wanted]
        logger.debug("Filtered risk zones by state=%s -> %d match(es)", state, len(records))

    zones = [RiskZone(status=band_for_score(record["riskScore"]), **record) for record in records]
    logger.debug("Returning %d risk zone(s)", len(zones))
    return zones
