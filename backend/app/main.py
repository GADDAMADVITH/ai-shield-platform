"""AI Shield FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_router
from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.middleware.cors import setup_cors

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings)
    logger.info(
        "Starting %s (env=%s, debug=%s)",
        settings.app_name,
        settings.app_env,
        settings.debug,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def _custom_openapi(app: FastAPI) -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Access token from /api/v1/auth/login or /api/v1/auth/register",
    }
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            # Mark routes that require HTTPBearer (Authorization header).
            for param in operation.get("parameters") or []:
                if param.get("name") == "authorization":
                    operation["security"] = [{"BearerAuth": []}]
                    break
    app.openapi_schema = schema
    return app.openapi_schema


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        description=(
            "AI Shield API. Authenticate via `/api/v1/auth/register` or "
            "`/api/v1/auth/login`, then send `Authorization: Bearer <access_token>`."
        ),
    )

    setup_cors(app, settings)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    app.openapi = lambda: _custom_openapi(app)  # type: ignore[method-assign]

    return app


app = create_app()
