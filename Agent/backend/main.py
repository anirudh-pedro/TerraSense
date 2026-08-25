import os
import uuid
import math
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

from models import Base, Report
from schemas import AlertResponse, AlertDetailResponse
from pipeline import process_image_pipeline

load_dotenv()

app = FastAPI(title="Landslide Image Verification & Alert")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB setup
DB_PATH = os.environ.get("DB_PATH", "sqlite:///./alerts.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Upload dir setup
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "../uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Haversine formula for distance
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Background Task
def run_pipeline_task(report_id: str, image_path: str):
    # Process pipeline
    final_state = process_image_pipeline(report_id, image_path, None)
    
    # Update DB
    db = SessionLocal()
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        report.status = final_state.get("status", "error")
        
        # Populate authenticity data
        if "authenticity_result" in final_state:
            auth_res = final_state["authenticity_result"]
            report.is_ai_generated = auth_res.is_ai_generated
            report.ai_confidence = auth_res.confidence
            report.ai_reasoning = auth_res.reasoning
            
        # Populate severity data if it passed
        if "severity_result" in final_state:
            sev_res = final_state["severity_result"]
            report.severity = sev_res.severity
            report.severity_confidence = sev_res.confidence
            report.affected_indicators = sev_res.affected_indicators
            report.severity_reasoning = sev_res.reasoning
            report.recommended_action = sev_res.recommended_action
            
        db.commit()
    db.close()

@app.post("/api/report")
async def create_report(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    device_timestamp: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Save file
    report_id = str(uuid.uuid4())
    ext = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
    file_path = os.path.join(UPLOAD_DIR, f"{report_id}.{ext}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())
        
    dt = None
    if device_timestamp:
        try:
            dt = datetime.fromisoformat(device_timestamp.replace('Z', '+00:00'))
        except ValueError:
            pass
            
    # Create DB record
    new_report = Report(
        id=report_id,
        image_path=file_path,
        latitude=latitude,
        longitude=longitude,
        device_timestamp=dt,
        status="processing"
    )
    db.add(new_report)
    db.commit()
    
    # Enqueue pipeline
    background_tasks.add_task(run_pipeline_task, report_id, file_path)
    
    return {"id": report_id, "status": "processing"}

@app.get("/api/alerts", response_model=List[AlertResponse])
def get_alerts(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    min_severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Report).filter(Report.status == "posted")
    
    if min_severity:
        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        try:
            min_idx = severities.index(min_severity.upper())
            allowed = severities[min_idx:]
            query = query.filter(Report.severity.in_(allowed))
        except ValueError:
            pass # ignore invalid severity
            
    # Order by severity then recency
    # For simplicity in SQLite, we might just fetch and sort in python
    reports = query.order_by(Report.created_at.desc()).all()
    
    results = []
    for r in reports:
        if lat is not None and lng is not None and radius_km is not None:
            dist = haversine(lat, lng, r.latitude, r.longitude)
            if dist > radius_km:
                continue
                
        # Make path accessible or mock a URL for now
        image_url = f"/uploads/{os.path.basename(r.image_path)}"
        
        results.append(AlertResponse(
            id=r.id,
            image_url=image_url,
            latitude=r.latitude,
            longitude=r.longitude,
            severity=r.severity,
            severity_confidence=r.severity_confidence,
            recommended_action=r.recommended_action,
            timestamp=r.created_at
        ))
        
    # Sort by severity (critical first)
    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    results.sort(key=lambda x: (severity_rank.get(x.severity, 0), x.timestamp), reverse=True)
    
    return results

@app.get("/api/alerts/{report_id}", response_model=AlertDetailResponse)
def get_alert_detail(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    image_url = f"/uploads/{os.path.basename(report.image_path)}"
    
    return AlertDetailResponse(
        id=report.id,
        image_url=image_url,
        latitude=report.latitude,
        longitude=report.longitude,
        device_timestamp=report.device_timestamp,
        created_at=report.created_at,
        status=report.status,
        is_ai_generated=report.is_ai_generated,
        ai_confidence=report.ai_confidence,
        ai_reasoning=report.ai_reasoning,
        severity=report.severity,
        severity_confidence=report.severity_confidence,
        affected_indicators=report.affected_indicators,
        severity_reasoning=report.severity_reasoning,
        recommended_action=report.recommended_action
    )
