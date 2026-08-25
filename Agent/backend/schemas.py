from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- API Schemas ---

class AlertResponse(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    severity: str
    severity_confidence: float
    recommended_action: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AlertDetailResponse(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    device_timestamp: Optional[datetime]
    created_at: datetime
    status: str
    is_ai_generated: Optional[bool]
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]
    severity: Optional[str]
    severity_confidence: Optional[float]
    affected_indicators: Optional[List[str]]
    severity_reasoning: Optional[str]
    recommended_action: Optional[str]

    class Config:
        from_attributes = True

# --- Groq Output Schemas ---

class AuthenticityCheckResult(BaseModel):
    is_ai_generated: bool = Field(description="True if the image is likely AI generated, False otherwise")
    confidence: float = Field(description="Confidence score from 0 to 100")
    reasoning: str = Field(description="Detailed reasoning for the assessment")

class SeverityAnalysisResult(BaseModel):
    severity: str = Field(description="One of: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(description="Confidence score from 0 to 100")
    affected_indicators: List[str] = Field(description="List of observed indicators, e.g., soil displacement, structural damage")
    reasoning: str = Field(description="Detailed reasoning for the severity classification")
    recommended_action: str = Field(description="Recommended immediate action based on the severity")
