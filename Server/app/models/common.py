"""Common schemas: coordinates, health, and the standard error envelope."""

from typing import Annotated

from pydantic import BaseModel, Field

# Coordinates are always [latitude, longitude] to match Leaflet on the frontend.
Coordinate = Annotated[
    list[float],
    Field(min_length=2, max_length=2, examples=[[25.8, 92.6]]),
]


class HealthResponse(BaseModel):
    """Backend health/liveness payload."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["TerraSense NER API"])
    version: str = Field(examples=["0.1.0"])
    environment: str = Field(examples=["development"])
    time: str = Field(description="Server time (ISO-8601, UTC).", examples=["2026-08-23T09:20:00+00:00"])


class ErrorDetail(BaseModel):
    """Machine-readable error code + human message."""

    code: str = Field(examples=["NOT_FOUND"])
    message: str = Field(examples=["Resource not found."])


class ErrorResponse(BaseModel):
    """Standard error envelope returned by every failed request."""

    error: ErrorDetail
