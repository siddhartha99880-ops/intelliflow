from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import logging

from app.core.config import get_settings

from app.api.routers import auth, workflows, executions, integrations, teams, api_keys, copilot


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            return await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logging.getLogger("intelliflow").info(
                "request completed",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(TimingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logging.getLogger("intelliflow").exception(
            "unhandled exception",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
    app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
    app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
    app.include_router(api_keys.router, prefix="/api/api-keys", tags=["api-keys"])
    app.include_router(copilot.router, prefix="/api/copilot", tags=["copilot"])

    @app.get("/healthz", include_in_schema=False)
    async def healthz():
        return {"status": "ok"}

    @app.on_event("startup")
    async def startup_create_tables():
        # MVP convenience: create tables automatically.
        # For production, use Alembic migrations.
        from app.core.database import engine, Base
        # Import model modules so SQLAlchemy registers metadata.
        import app.models.user  # noqa: F401
        import app.models.team  # noqa: F401
        import app.models.workflow  # noqa: F401
        import app.models.executions  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        import os

        from app.core.config import get_settings

        if get_settings().seed_demo_data or os.getenv("SEED_DEMO_DATA") == "1":
            from app.scripts.seed import seed as seed_fn

            await seed_fn()

    return app


app = create_app()

