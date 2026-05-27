from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings


def normalize_database_url(url: str) -> str:
    """Railway Postgres uses postgresql:// — SQLAlchemy async needs postgresql+asyncpg://."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Railway-hosted Postgres typically requires SSL.
    if ("railway.app" in url or "rlwy.net" in url) and "sslmode=" not in url:
        url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
    return url


class Settings(BaseSettings):
    # General
    app_name: str = "IntelliFlow API"
    environment: str = "development"
    debug: bool = True

    # Security
    secret_key: str = "CHANGE_ME_IN_PROD"
    access_token_expire_minutes: int = 60 * 24
    jwt_algorithm: str = "HS256"

    # Database
    database_url: AnyUrl | str = "sqlite+aiosqlite:///./intelliflow.db"

    # Redis / Celery (Railway injects REDIS_URL when Redis is linked)
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    # OpenAI / LLM
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    # Misc — set to your Netlify URL in production, e.g. ["https://your-app.netlify.app"]
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    # Seed demo user/workflow on startup (set 0 in production after first deploy)
    seed_demo_data: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db(cls, v: Any) -> Any:
        if isinstance(v, str):
            return normalize_database_url(v)
        return v

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("["):
                return json.loads(v)
            return [part.strip() for part in v.split(",") if part.strip()]
        return []

    @field_validator("seed_demo_data", mode="before")
    @classmethod
    def _parse_seed_flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return bool(v)

    def get_celery_broker(self) -> str:
        if self.celery_broker_url:
            return self.celery_broker_url
        if "sqlite" in str(self.database_url) and self.redis_url == "redis://redis:6379/0":
            return "sqla+sqlite:///./celerybroker.db"
        return self.redis_url

    def get_celery_backend(self) -> str:
        if self.celery_result_backend:
            return self.celery_result_backend
        if "sqlite" in str(self.database_url) and self.redis_url == "redis://redis:6379/0":
            return "db+sqlite:///./celeryresults.db"
        return self.redis_url



@lru_cache
def get_settings() -> Settings:
    return Settings()
