"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, connections, dashboard, health, notifications, projects, reports, scans

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(connections.router)
api_router.include_router(scans.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(dashboard.router)
