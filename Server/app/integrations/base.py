"""Base abstractions for external data providers.

New sources (soil moisture, terrain/DEM, satellite, landslide history) subclass
:class:`ExternalDataProvider`, reuse :meth:`_get_json` for HTTP with consistent
timeout/error handling, and return their own normalized dataclass.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    """Catalog of external data sources feeding the ingestion pipeline."""

    WEATHER = "weather"
    SOIL_MOISTURE = "soil_moisture"
    TERRAIN = "terrain"
    SATELLITE = "satellite"
    LANDSLIDE_HISTORY = "landslide_history"


class ProviderError(Exception):
    """Raised when an upstream provider fails or is misconfigured.

    ``status_code`` is the HTTP status the API should surface (502 upstream
    failure, 503 not configured).
    """

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ExternalDataProvider(ABC):
    """Common contract + HTTP helper for all external data providers."""

    name: str = "provider"
    source: DataSource

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._timeout = timeout

    @property
    @abstractmethod
    def configured(self) -> bool:
        """Whether the provider has the credentials/config it needs."""

    def _get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        """GET JSON with uniform timeout and error handling.

        Raises :class:`ProviderError` (never leaks httpx exceptions) so callers
        get a consistent, catchable failure with an HTTP status.
        """
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("%s upstream returned HTTP %s", self.name, status)
            if status in (401, 403):
                raise ProviderError(f"{self.name} rejected the request (check API key).", 502) from exc
            raise ProviderError(f"{self.name} returned HTTP {status}.", 502) from exc
        except httpx.HTTPError as exc:
            logger.warning("%s request failed: %s", self.name, exc)
            raise ProviderError(f"{self.name} is unreachable.", 502) from exc
