"""Region metadata service."""

import logging

from app.models.region import RegionMeta
from app.services import mock_data

logger = logging.getLogger(__name__)


def get_region_meta() -> RegionMeta:
    """Return region banner + default map view."""
    logger.debug("Fetching region meta")
    return RegionMeta(**mock_data.REGION_META)
