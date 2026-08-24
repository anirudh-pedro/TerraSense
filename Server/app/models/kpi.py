"""KPI summary schemas — GET /api/kpis/summary."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeltaDir, RiskStatus


class KpiDelta(BaseModel):
    """Change indicator (chip) for a KPI card."""

    dir: DeltaDir = Field(description="Direction of change.")
    text: str = Field(description="Short change description.", examples=["+3 today"])


class KpiCard(BaseModel):
    """A single Risk Overview card."""

    value: int = Field(description="Current count.", examples=[12])
    note: str = Field(description="Sub-caption under the number.")
    band: RiskStatus = Field(description="Accent color band for the card.")
    delta: KpiDelta
    trend: list[int] = Field(description="Recent readings for the mini sparkline.")


class KpiSummary(BaseModel):
    """The four Risk Overview KPI cards on the dashboard."""

    criticalZones: KpiCard
    highRiskZones: KpiCard
    activeAlerts: KpiCard
    roadsAffected: KpiCard

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "criticalZones": {
                    "value": 12,
                    "note": "Requires immediate attention",
                    "band": "CRITICAL",
                    "delta": {"dir": "up", "text": "+3 today"},
                    "trend": [6, 7, 7, 8, 9, 10, 11, 12],
                },
                "highRiskZones": {
                    "value": 28,
                    "note": "Elevated across NER",
                    "band": "HIGH",
                    "delta": {"dir": "up", "text": "+7 since yesterday"},
                    "trend": [18, 19, 21, 20, 23, 25, 26, 28],
                },
                "activeAlerts": {
                    "value": 9,
                    "note": "3 critical",
                    "band": "CRITICAL",
                    "delta": {"dir": "up", "text": "+2 this hour"},
                    "trend": [4, 5, 5, 6, 6, 7, 8, 9],
                },
                "roadsAffected": {
                    "value": 17,
                    "note": "5 currently blocked",
                    "band": "HIGH",
                    "delta": {"dir": "flat", "text": "No change"},
                    "trend": [15, 16, 16, 17, 17, 16, 17, 17],
                },
            }
        }
    )
