"""Aggregate API router — mounts every route module under one router."""

from fastapi import APIRouter

from app.api.routes import ai_prediction, health, kpis, region, risk_zones, weather

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(region.router)
api_router.include_router(kpis.router)
api_router.include_router(risk_zones.router)
api_router.include_router(weather.router)
api_router.include_router(ai_prediction.router)
