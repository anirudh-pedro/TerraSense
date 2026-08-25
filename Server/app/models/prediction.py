"""AI risk prediction schemas — GET /api/ai/prediction."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RiskStatus


class PredictionFactor(BaseModel):
    """One of the five model-derived contributing factors."""

    name: str = Field(examples=["Heavy Rainfall"])
    level: str = Field(description="Human-readable level label.", examples=["High"])
    weight: float = Field(description="SHAP-derived intensity 0–1.", ge=0, le=1, examples=[0.9])


class PredictionTrendPoint(BaseModel):
    """A single point of the 24-hour risk trend."""

    time: str = Field(examples=["14:00"])
    risk: int = Field(description="Risk score at that time (0–100).", ge=0, le=100, examples=[74])


class AiPredictionResponse(BaseModel):
    """AI Risk Prediction panel payload (gauge + factors + 24h trend)."""

    district: Optional[str] = Field(default=None, examples=["Aizawl"])
    state: Optional[str] = Field(default=None, examples=["Mizoram"])
    riskScore: int = Field(description="Blended model risk score.", ge=0, le=100, examples=[87])
    status: RiskStatus = Field(description="Severity band (model thresholds).")
    summary: str
    predictionWindow: str = Field(examples=["Next 6–12 hours"])
    factors: list[PredictionFactor]
    trend: list[PredictionTrendPoint]
    # Data-quality signal (not in the original contract; frontend ignores it):
    # "real" if built from logged 2-hourly history, "simulated" for the ramp fallback.
    trend_source: Optional[str] = Field(default=None, examples=["simulated"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "district": "Aizawl",
                "state": "Mizoram",
                "riskScore": 87,
                "status": "CRITICAL",
                "summary": "High probability of slope failure within the next 6–12 hours.",
                "predictionWindow": "Next 6–12 hours",
                "factors": [
                    {"name": "Heavy Rainfall", "level": "High", "weight": 0.9},
                    {"name": "Soil Moisture", "level": "Very High", "weight": 0.95},
                    {"name": "Slope", "level": "38°", "weight": 0.82},
                    {"name": "Historical Activity", "level": "High", "weight": 0.78},
                    {"name": "Terrain Stability", "level": "Low", "weight": 0.85},
                ],
                "trend": [{"time": "14:00", "risk": 74}, {"time": "16:00", "risk": 87}],
                "trend_source": "simulated",
            }
        }
    )
