"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_INSECURE_JWT_DEFAULTS = {
    "change-me-in-production-use-a-long-random-secret",
    "replace-me-with-a-long-random-production-secret",
}


class ConfigurationError(ValueError):
    """Raised when settings fail production/runtime validation."""


class Settings(BaseSettings):
    """Central settings for the AI Shield backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Shield"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS — comma-separated string in env (NoDecode avoids JSON-only parsing)
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ]
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_shield"

    # Auth / JWT
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Scan execution (BackgroundTasks). Set false in tests to assert queued/cancel.
    scan_auto_execute: bool = True

    # Startup / readiness
    startup_validate_database: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return []
            if cleaned.startswith("["):
                import json

                return json.loads(cleaned)
            return [origin.strip() for origin in cleaned.split(",") if origin.strip()]
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("DATABASE_URL must not be empty")
        if not cleaned.startswith(("postgresql", "postgres", "sqlite")):
            raise ValueError("DATABASE_URL must be a PostgreSQL (or sqlite test) URL")
        return cleaned

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_present(cls, value: str) -> str:
        if not (value or "").strip():
            raise ValueError("JWT_SECRET_KEY must not be empty")
        return value

    @model_validator(mode="after")
    def validate_production_guards(self) -> Self:
        if self.app_env == "production":
            if self.debug:
                raise ConfigurationError("DEBUG must be false when APP_ENV=production")
            if self.jwt_secret_key.strip() in _INSECURE_JWT_DEFAULTS:
                raise ConfigurationError(
                    "JWT_SECRET_KEY must be changed from the insecure default in production"
                )
            if len(self.jwt_secret_key.strip()) < 32:
                raise ConfigurationError(
                    "JWT_SECRET_KEY must be at least 32 characters in production"
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_for_runtime(self) -> None:
        """Explicit runtime validation used by startup and readiness probes."""
        if not self.database_url.strip():
            raise ConfigurationError("DATABASE_URL is required")
        if not self.jwt_secret_key.strip():
            raise ConfigurationError("JWT_SECRET_KEY is required")
        if self.is_production:
            # Re-run production guards explicitly for readiness/startup paths.
            if self.debug:
                raise ConfigurationError("DEBUG must be false when APP_ENV=production")
            if self.jwt_secret_key.strip() in _INSECURE_JWT_DEFAULTS:
                raise ConfigurationError(
                    "JWT_SECRET_KEY must be changed from the insecure default in production"
                )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
