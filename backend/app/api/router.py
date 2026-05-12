"""Aggregate all API routers into a single router."""

from fastapi import APIRouter

from app.api.assets import router as assets_router
from app.api.dashboard import router as dashboard_router
from app.api.documents import router as documents_router
from app.api.events import router as events_router
from app.api.ingestion import router as ingestion_router

api_router = APIRouter()
api_router.include_router(documents_router)
api_router.include_router(events_router)
api_router.include_router(assets_router)
api_router.include_router(ingestion_router)
api_router.include_router(dashboard_router)
