"""Risk zone schema — GET /api/risk-zones."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import Coordinate
from app.models.enums import RiskStatus


class RiskZone(BaseModel):
    """A circular landslide-risk zone with its full environmental payload.

    `status` is derived server-side from `riskScore`; it is never stored or
    trusted from input data.
    """

    id: str = Field(description="Stable zone identifier.", examples=["zone-aizawl"])
    district: str = Field(examples=["Aizawl"])
    state: str = Field(examples=["Mizoram"])
    center: Coordinate = Field(description="Zone centroid [lat, lng].")
    radius: int = Field(description="Zone radius in meters.", gt=0, examples=[9000])
    riskScore: int = Field(description="AI risk score.", ge=0, le=100, examples=[87])
    status: RiskStatus = Field(description="Severity band derived from riskScore.")
    rainfall: int = Field(description="Rainfall over 24h (mm).", ge=0, examples=[182])
    soilMoisture: int = Field(description="Soil moisture saturation (%).", ge=0, le=100, examples=[89])
    slope: int = Field(description="Terrain slope (degrees).", ge=0, le=90, examples=[38])
    elevation: int = Field(description="Elevation (meters).", examples=[1240])
    predictionWindow: str = Field(
        description="Human-readable prediction window.", examples=["Next 6–12 hours"]
    )
    populationExposed: int = Field(description="People within the zone.", ge=0, examples=[4820])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "zone-aizawl",
                "district": "Aizawl",
                "state": "Mizoram",
                "center": [23.7271, 92.7176],
                "radius": 9000,
                "riskScore": 87,
                "status": "CRITICAL",
                "rainfall": 182,
                "soilMoisture": 89,
                "slope": 38,
                "elevation": 1240,
                "predictionWindow": "Next 6–12 hours",
                "populationExposed": 4820,
            }
        }
    )
