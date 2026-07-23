"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, connections, health, projects, scans

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(connections.router)
api_router.include_router(scans.router)
