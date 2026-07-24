"""Health and readiness endpoints."""

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import engine
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe — returns healthy when the process is running."""
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def ready(response: Response) -> ReadinessResponse:
    """Readiness probe — verifies configuration and database connectivity."""
    settings = get_settings()
    checks: dict[str, object] = {
        "configuration": "ok",
        "database": "skipped",
    }

    try:
        settings.validate_for_runtime()
    except Exception as exc:  # noqa: BLE001 — surface as not ready
        logger.warning("Readiness configuration check failed: %s", exc)
        checks["configuration"] = {"status": "error", "detail": str(exc)}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="not_ready", checks=checks)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness database check failed: %s", exc)
        checks["database"] = {"status": "error", "detail": str(exc)}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="not_ready", checks=checks)

    return ReadinessResponse(status="ready", checks=checks)
