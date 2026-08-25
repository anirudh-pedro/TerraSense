"""Weather schemas — GET /api/weather."""

from pydantic import BaseModel, ConfigDict, Field


class WeatherForecastPoint(BaseModel):
    """A single point in the rainfall forecast series."""

    time: str = Field(description="Time label (e.g. 'Now', '15:00').", examples=["15:00"])
    rain: int = Field(description="Rainfall intensity (mm/hr).", ge=0, examples=[46])


class WeatherResponse(BaseModel):
    """Current conditions + short-term rainfall forecast for a district."""

    district: str = Field(examples=["Aizawl"])
    temperature: int = Field(description="Air temperature (°C).", examples=[24])
    humidity: int = Field(description="Relative humidity (%).", ge=0, le=100, examples=[91])
    rainfall: int = Field(description="Current rainfall intensity (mm/hr).", ge=0, examples=[42])
    wind: int = Field(description="Wind speed (km/h).", ge=0, examples=[18])
    warning: str | None = Field(
        default=None,
        description="Heavy-rainfall warning banner text, or null when none.",
        examples=["Heavy rainfall expected over the next several hours"],
    )
    forecast: list[WeatherForecastPoint] = Field(description="Rainfall forecast series.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "district": "Aizawl",
                "temperature": 24,
                "humidity": 91,
                "rainfall": 42,
                "wind": 18,
                "warning": "Heavy rainfall expected over the next several hours",
                "forecast": [
                    {"time": "Now", "rain": 42},
                    {"time": "15:00", "rain": 46},
                    {"time": "18:00", "rain": 51},
                ],
            }
        }
    )
