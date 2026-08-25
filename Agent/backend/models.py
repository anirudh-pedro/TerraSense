import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    device_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # status: "processing", "posted", "rejected"
    status = Column(String, default="processing")
    
    # AI Authenticity checks
    is_ai_generated = Column(Boolean, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(String, nullable=True)
    
    # Severity Analysis
    severity = Column(String, nullable=True) # LOW, MEDIUM, HIGH, CRITICAL
    severity_confidence = Column(Float, nullable=True)
    affected_indicators = Column(JSON, nullable=True)
    severity_reasoning = Column(String, nullable=True)
    recommended_action = Column(String, nullable=True)
