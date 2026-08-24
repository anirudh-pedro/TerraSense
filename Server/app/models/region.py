"""Region metadata schema — GET /api/region/meta."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import Coordinate


class RegionMeta(BaseModel):
    """Region banner information and default map view for the frontend."""

    name: str = Field(description="Region label shown in the header.", examples=["NER"])
    lastUpdated: str = Field(
        description="Human-friendly freshness label (e.g. '2 min ago').",
        examples=["2 min ago"],
    )
    center: Coordinate = Field(description="Default map center [lat, lng].")
    zoom: int = Field(description="Default Leaflet zoom level.", ge=0, le=20, examples=[6])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "NER",
                "lastUpdated": "2 min ago",
                "center": [25.8, 92.6],
                "zoom": 6,
            }
        }
    )
