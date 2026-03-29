# app/main.py
"""
FastAPI app factory.
Lifespan handles: DB connection, scheduler start, Lava health check.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import auth, backlog, blockers, health, reports, review, sprint, standup, voice
from app.config import settings
from app.db.mongo import close_mongo, connect_mongo
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.middleware import LoggingMiddleware, RequestIDMiddleware

log = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────────────────────
    log.info("app.startup", env=settings.ENV)

    # Connect to MongoDB Atlas
    await connect_mongo()
    log.info("app.mongo_connected")

    # Start APScheduler (background jobs)
    await start_scheduler()
    log.info("app.scheduler_started")

    # Warm up context snapshot (don't wait for first cron tick)
    from app.services.context_builder import build_context_snapshot

    try:
        await build_context_snapshot()
        log.info("app.context_warmed")
    except Exception as e:
        log.warning("app.context_warmup_failed", error=str(e))

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    await stop_scheduler()
    await close_mongo()
    log.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="PilotPM API",
        version="1.0.0",
        description="AI PM Orchestrator — YHack 2026",
        docs_url="/docs" if settings.ENV != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # ── Rate limiter ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Middleware (order matters — outermost first) ───────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "Something went wrong. Please try again.",
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": str(exc)},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(standup.router, prefix="/api/v1/standup", tags=["standup"])
    app.include_router(blockers.router, prefix="/api/v1/blockers", tags=["blockers"])
    app.include_router(sprint.router, prefix="/api/v1/sprint", tags=["sprint"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
    app.include_router(backlog.router, prefix="/api/v1/backlog", tags=["backlog"])
    app.include_router(review.router, prefix="/api/v1/review", tags=["review"])

    return app


app = create_app()
