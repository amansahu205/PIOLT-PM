# BACKEND_STRUCTURE.md — Backend Architecture

> **Version**: 1.0 | **Last Updated**: March 28, 2026
> **Project**: PilotPM
> **References**: PRD.md v1.0, AI_ARCHITECTURE.md v1.0
> **Stack**: Python 3.11 + FastAPI + Motor async MongoDB + LangGraph + APScheduler

---

## 0. Stack Decisions

> PilotPM uses MongoDB (not PostgreSQL) — the data is document-shaped (context snapshots,
> agent digests, review queue items, call transcripts). No ORM needed. Motor is the async
> MongoDB driver. APScheduler handles background jobs (standup at 9am, report at 5pm Friday).

| Component | Choice | Reason |
|-----------|--------|--------|
| Framework | FastAPI | Async-native, auto OpenAPI docs, fast to scaffold |
| Database | MongoDB Atlas (Motor async) | Document-shaped data, free tier, no schema migrations |
| Auth | JWT (python-jose) | Simple, stateless, hardcoded demo user — no Auth0 |
| Agent orchestration | LangGraph | Multi-agent workflow graph |
| Background jobs | APScheduler | Lightweight, in-process cron — no Redis/worker needed |
| AI inference | Lava forward (OpenAI upstream by default) + optional Gemini direct fallback | See AI_ARCHITECTURE.md |
| Voice | ElevenLabs Conversational AI + Twilio | See AI_ARCHITECTURE.md |
| Analytics | Hex API | Sprint dashboards |
| Logging | structlog JSON | Machine-readable, correlates with agent reasoning |

---

## 1. Request Lifecycle

```
HTTP REQUEST
    │
    ▼
[Uvicorn ASGI]
    │
    ▼
[Middleware Stack]  ← ordered, see Section 11
    │  CORSMiddleware
    │  RequestIDMiddleware     ← inject X-Request-ID header
    │  LoggingMiddleware       ← log method, path, status, latency
    │  RateLimitMiddleware     ← slowapi, 60 req/min per IP
    │
    ▼
[FastAPI Router]
    │
    ├─ Public routes (/health, /auth/login, /)
    │
    └─ Protected routes (/api/v1/*)
           │
           ▼
       [get_current_user]     ← JWT dependency, validates token
           │
           ▼
       [Route Handler]        ← validates input schema (Pydantic)
           │                    NO business logic here
           ▼
       [Service Layer]        ← business logic, LangGraph trigger
           │                    ownership checks, action staging
           ▼
       [Repository Layer]     ← MongoDB queries ONLY
           │                    NO business logic here
           ▼
       [Motor / MongoDB Atlas]
           │
           ▼
       [Response]             ← Pydantic output schema
           │
           ▼
[Middleware Stack]             ← response logging
    │
    ▼
HTTP RESPONSE

PARALLEL: Background jobs (APScheduler)
    │
    ├─ standup_job()           ← daily 9am → triggers StandupAgent
    ├─ blocker_poll_job()      ← every 15 min → triggers BlockerAgent
    ├─ context_refresh_job()   ← every 15 min → ContextBuilder
    └─ report_job()            ← Friday 5pm → triggers ReportAgent
```

---

## 2. Project Structure

```
pilotpm/
├── app/
│   ├── main.py                    ← FastAPI app factory + lifespan
│   ├── config.py                  ← Settings (pydantic-settings)
│   ├── dependencies.py            ← get_current_user, get_db
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            ← POST /auth/login, POST /auth/refresh
│   │   │   ├── standup.py         ← F-001 endpoints
│   │   │   ├── blockers.py        ← F-002 endpoints
│   │   │   ├── sprint.py          ← F-003 endpoints
│   │   │   ├── reports.py         ← F-004 endpoints
│   │   │   ├── voice.py           ← F-005 Twilio webhook + context
│   │   │   ├── backlog.py         ← F-010 endpoints
│   │   │   ├── review.py          ← F-011 review queue endpoints
│   │   │   └── health.py          ← GET /health
│   │
│   ├── services/
│   │   ├── auth_service.py        ← JWT create/decode, login verify
│   │   ├── standup_service.py     ← F-001 business logic
│   │   ├── blocker_service.py     ← F-002 business logic
│   │   ├── sprint_service.py      ← F-003 business logic
│   │   ├── report_service.py      ← F-004 business logic
│   │   ├── voice_service.py       ← F-005 context assembly
│   │   ├── backlog_service.py     ← F-010 business logic
│   │   ├── review_service.py      ← F-011 approve/reject logic
│   │   ├── context_builder.py     ← shared context snapshot
│   │   └── orchestrator.py        ← LangGraph entry point
│   │
│   ├── repositories/
│   │   ├── base.py                ← async CRUD base
│   │   ├── standup_repo.py
│   │   ├── blocker_repo.py
│   │   ├── sprint_repo.py
│   │   ├── report_repo.py
│   │   ├── review_repo.py
│   │   ├── context_repo.py
│   │   └── transcript_repo.py     ← voice call transcripts
│   │
│   ├── integrations/
│   │   ├── github_service.py      ← GitHub REST API calls
│   │   ├── slack_service.py       ← Slack Web API calls
│   │   ├── monday_service.py      ← Monday.com API + MCP calls
│   │   ├── gmail_service.py       ← Gmail MCP calls
│   │   ├── calendar_service.py    ← Google Calendar MCP calls
│   │   ├── hex_service.py         ← Hex API calls
│   │   ├── elevenlabs_service.py  ← ElevenLabs Conversational AI
│   │   └── twilio_service.py      ← Twilio call handling
│   │
│   ├── lib/
│   │   ├── llm.py                 ← AI router (see AI_ARCHITECTURE.md)
│   │   ├── prompts.py             ← All prompts (see AI_ARCHITECTURE.md)
│   │   ├── retry.py               ← llm_retry decorator
│   │   ├── cost.py                ← Cost tracking
│   │   └── guardrails.py          ← Input/output validation
│   │
│   ├── models/
│   │   ├── auth.py                ← LoginRequest, TokenResponse
│   │   ├── standup.py             ← StandupDigest, EngineerCard
│   │   ├── blocker.py             ← BlockerCard, BlockerSeverity
│   │   ├── sprint.py              ← SprintPlan, TicketScore
│   │   ├── report.py              ← StatusReport, ReportDraft
│   │   ├── review.py              ← ReviewAction, ActionType
│   │   ├── voice.py               ← CallTranscript, VoiceContext
│   │   └── common.py              ← APIResponse, PaginatedResponse
│   │
│   ├── jobs/
│   │   ├── scheduler.py           ← APScheduler setup
│   │   ├── standup_job.py         ← Daily 9am trigger
│   │   ├── blocker_job.py         ← Every 15min trigger
│   │   ├── context_job.py         ← Every 15min context refresh
│   │   └── report_job.py          ← Friday 5pm trigger
│   │
│   └── db/
│       ├── mongo.py               ← Motor client + collection helpers
│       └── indexes.py             ← MongoDB index definitions
│
├── tests/
│   ├── test_standup.py
│   ├── test_blockers.py
│   ├── test_sprint.py
│   └── agents/                    ← agent regression tests
│
├── .env                           ← never commit
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 3. App Factory (`main.py`)

```python
# app/main.py
"""
FastAPI app factory.
Lifespan handles: DB connection, scheduler start, Lava health check.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.db.mongo import connect_mongo, close_mongo
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.api.v1 import auth, standup, blockers, sprint, reports, voice, backlog, review, health
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
        log.error("unhandled_exception",
                  path=request.url.path,
                  method=request.method,
                  error=str(exc),
                  exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error",
                     "message": "Something went wrong. Please try again."},
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
```

---

## 4. Config (`config.py`)

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ENV: str = "development"

    # Auth (hardcoded demo — no user DB)
    DEMO_EMAIL: str
    DEMO_PASSWORD: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours — covers full hackathon

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB: str = "pilotpm"

    # AI — Lava forward proxy (Bearer secret; POST /v1/forward?u=upstream URL)
    LAVA_API_KEY: str
    LAVA_BASE: str = "https://api.lava.so"
    LAVA_FORWARD_UPSTREAM: str = "https://api.openai.com/v1/chat/completions"
    LAVA_MODEL_PRIMARY: str = "gpt-4o-mini"
    LAVA_MODEL_FALLBACK: str = "gpt-4o"
    GEMINI_API_KEY: str = ""                  # optional last-resort if Lava fails
    GEMINI_MODEL: str = "gemini-3-flash-preview"

    # K2 Think V2 — MBZUAI sponsor, direct API
    K2_API_KEY: str
    K2_API_BASE: str = "https://api.k2think.ai"

    # Integrations
    GITHUB_TOKEN: str
    SLACK_BOT_TOKEN: str
    MONDAY_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_AGENT_ID: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE: str
    HEX_API_KEY: str

    # Stakeholder emails (comma-separated)
    STAKEHOLDER_EMAILS: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://pilotpm.vercel.app",
    ]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

---

## 5. Database Setup (`db/mongo.py`)

```python
# app/db/mongo.py
"""
Async MongoDB client via Motor.
Single client instance — reused across all requests.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import structlog

log = structlog.get_logger()

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
    )
    _db = _client[settings.MONGODB_DB]
    # Verify connection
    await _client.admin.command("ping")
    log.info("mongo.connected", db=settings.MONGODB_DB)
    # Ensure indexes
    from app.db.indexes import ensure_indexes
    await ensure_indexes(_db)


async def close_mongo():
    global _client
    if _client:
        _client.close()
        log.info("mongo.disconnected")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not connected — call connect_mongo() first")
    return _db


def get_collection(name: str):
    return get_db()[name]
```

```python
# app/db/indexes.py
"""MongoDB indexes — run on startup."""

async def ensure_indexes(db):
    # Context snapshots — TTL 1 hour
    await db.project_context.create_index("refreshed_at", expireAfterSeconds=3600)

    # Blockers — query by severity + status
    await db.blockers.create_index([("severity", 1), ("status", 1)])
    await db.blockers.create_index("engineer")
    await db.blockers.create_index("detected_at")

    # Review queue — query pending actions
    await db.review_queue.create_index([("status", 1), ("created_at", -1)])
    await db.review_queue.create_index("workflow_type")

    # Standup digests — TTL 7 days
    await db.standup_digests.create_index("generated_at", expireAfterSeconds=604800)

    # Voice transcripts — TTL 30 days
    await db.call_transcripts.create_index("called_at", expireAfterSeconds=2592000)

    # Sprint plans
    await db.sprint_plans.create_index([("sprint_number", -1)])
    await db.sprint_plans.create_index("status")
```

---

## 6. Dependency Injection (`dependencies.py`)

```python
# app/dependencies.py
"""
FastAPI dependencies.
All protected routes use: Depends(get_current_user)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import decode_jwt
from app.db.mongo import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Validate JWT from Authorization: Bearer <token> header.
    Returns user dict: {"email": "pm@pilotpm.demo", "role": "pm"}
    Raises 401 if invalid or expired.
    """
    token = credentials.credentials
    payload = decode_jwt(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_db_dep() -> AsyncIOMotorDatabase:
    """Yield MongoDB database instance."""
    return get_db()


# Type alias for cleaner route signatures
CurrentUser = Depends(get_current_user)
DB = Depends(get_db_dep)
```

---

## 7. Auth Service (`services/auth_service.py`)

```python
# app/services/auth_service.py
"""
Auth service for PilotPM demo.
No user database — single hardcoded PM account from .env.
JWT signed with HS256.
"""

from datetime import datetime, UTC, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
import structlog

log = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_USER = {
    "email": settings.DEMO_EMAIL,
    "role": "pm",
    "name": "Aman",
}


def verify_credentials(email: str, password: str) -> bool:
    """Check email + password against .env values."""
    return (
        email == settings.DEMO_EMAIL
        and password == settings.DEMO_PASSWORD
    )


def create_jwt(user: dict) -> str:
    """Create a signed JWT for the PM user."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user["email"],
        "role": user["role"],
        "name": user["name"],
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict | None:
    """Decode and validate JWT. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        log.warning("auth.jwt_invalid", error=str(e))
        return None
```

---

## 8. Complete API Endpoint Catalog

### Auth

| Method | Path | Auth | Description | Request Body | Response |
|--------|------|------|-------------|-------------|----------|
| `POST` | `/auth/login` | None | Login with demo credentials | `LoginRequest` | `TokenResponse` |
| `POST` | `/auth/refresh` | JWT | Refresh expiring token | — | `TokenResponse` |

### Health

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/health` | None | Liveness check | `{"status": "ok", "gemini_via_lava": bool, "mongo": bool}` (legacy key name for LLM path) |

### Standup (F-001)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/standup/today` | JWT | Get today's digest (cached or generate) | `StandupDigest` |
| `POST` | `/api/v1/standup/generate` | JWT | Force-regenerate digest | `StandupDigest` |
| `GET` | `/api/v1/standup/history` | JWT | Last 7 digests | `list[StandupDigest]` |

### Blockers (F-002)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/blockers` | JWT | All active blockers | `list[BlockerCard]` |
| `POST` | `/api/v1/blockers/scan` | JWT | Force-scan for new blockers | `list[BlockerCard]` |
| `PATCH` | `/api/v1/blockers/{id}/dismiss` | JWT | Dismiss a blocker | `BlockerCard` |
| `GET` | `/api/v1/blockers/history` | JWT | Resolved blockers (last 7 days) | `list[BlockerCard]` |

### Sprint (F-003)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/sprint/current` | JWT | Current sprint status | `SprintStatus` |
| `GET` | `/api/v1/sprint/draft` | JWT | Get AI draft for next sprint | `SprintPlan` |
| `POST` | `/api/v1/sprint/draft/generate` | JWT | Generate new sprint draft | `SprintPlan` |
| `PATCH` | `/api/v1/sprint/draft/tickets` | JWT | Update ticket selection/assignment | `SprintPlan` |
| `POST` | `/api/v1/sprint/approve` | JWT | Approve + push to Monday.com | `SprintApprovalResult` |

### Reports (F-004)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/reports/current` | JWT | This week's report (draft or sent) | `StatusReport` |
| `POST` | `/api/v1/reports/generate` | JWT | Generate report now | `StatusReport` |
| `PATCH` | `/api/v1/reports/{id}/edit` | JWT | Edit email body | `StatusReport` |
| `POST` | `/api/v1/reports/{id}/send` | JWT | Send via Gmail MCP | `SendResult` |
| `GET` | `/api/v1/reports/history` | JWT | Past 4 reports | `list[StatusReport]` |

### Voice (F-005)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `POST` | `/api/v1/voice/webhook/inbound` | Twilio sig | Twilio inbound call webhook | TwiML XML |
| `GET` | `/api/v1/voice/context` | JWT | Current voice agent context | `VoiceContext` |
| `GET` | `/api/v1/voice/transcripts` | JWT | Last 10 call transcripts | `list[CallTranscript]` |

### Backlog (F-010)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/backlog` | JWT | Scored + ranked backlog | `list[ScoredTicket]` |
| `POST` | `/api/v1/backlog/score` | JWT | Re-score backlog with K2 | `list[ScoredTicket]` |

### Review Queue (F-011)

| Method | Path | Auth | Description | Response |
|--------|------|------|-------------|----------|
| `GET` | `/api/v1/review` | JWT | All pending actions | `list[ReviewAction]` |
| `POST` | `/api/v1/review/{id}/approve` | JWT | Approve + execute action | `ActionResult` |
| `POST` | `/api/v1/review/approve-batch` | JWT | Approve multiple actions | `list[ActionResult]` |
| `POST` | `/api/v1/review/{id}/reject` | JWT | Reject action with reason | `ReviewAction` |
| `PATCH` | `/api/v1/review/{id}/edit` | JWT | Edit action content | `ReviewAction` |
| `GET` | `/api/v1/review/count` | JWT | Pending action count (for badge) | `{"count": int}` |

---

## 9. Router Pattern

```python
# app/api/v1/blockers.py
"""
Blocker Radar router — F-002.
Pattern: thin router → service → repository.
No business logic or DB queries here.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user, get_db_dep
from app.services.blocker_service import BlockerService
from app.models.blocker import BlockerCard, DismissRequest
from app.models.common import APIResponse
import structlog

log = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=list[BlockerCard])
async def get_blockers(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get all active blockers. Returns empty list if none."""
    try:
        return await BlockerService.get_active_blockers(db)
    except Exception as e:
        log.error("blockers.get_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch blockers")


@router.post("/scan", response_model=list[BlockerCard])
async def scan_blockers(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Force a blocker scan across GitHub + Slack + Monday.com."""
    try:
        return await BlockerService.run_blocker_scan(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("blockers.scan_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Blocker scan failed")


@router.patch("/{blocker_id}/dismiss", response_model=BlockerCard)
async def dismiss_blocker(
    blocker_id: str,
    body: DismissRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Dismiss a blocker. Logs reason for agent improvement."""
    blocker = await BlockerService.dismiss(blocker_id, body.reason, db)
    if not blocker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blocker {blocker_id} not found",
        )
    return blocker


@router.get("/history", response_model=list[BlockerCard])
async def get_blocker_history(
    days: int = 7,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get resolved blockers from the last N days."""
    return await BlockerService.get_resolved(days=days, db=db)
```

---

## 10. Service Layer Pattern

```python
# app/services/blocker_service.py
"""
Blocker service — all business logic for F-002.
No DB queries here — delegate to BlockerRepository.
No HTTP calls here — delegate to integrations/*.
"""

from datetime import datetime, UTC
from app.repositories.blocker_repo import BlockerRepository
from app.integrations.github_service import GitHubService
from app.integrations.slack_service import SlackService
from app.integrations.monday_service import MondayService
from app.services.review_service import ReviewService
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.guardrails import InputGuardrails
from app.lib.retry import llm_retry
from app.models.blocker import BlockerCard, BlockerStatus, BlockerSeverity
import json
import structlog

log = structlog.get_logger()


class BlockerService:

    @staticmethod
    async def get_active_blockers(db) -> list[BlockerCard]:
        """Return all non-dismissed blockers."""
        return await BlockerRepository.find_active(db)

    @staticmethod
    async def get_resolved(days: int, db) -> list[BlockerCard]:
        return await BlockerRepository.find_resolved(days=days, db=db)

    @staticmethod
    async def dismiss(blocker_id: str, reason: str | None, db) -> BlockerCard | None:
        """
        Dismiss a blocker. Log reason to MongoDB for future model improvement.
        Business logic: dismissed blockers are kept for 7 days then TTL-deleted.
        """
        blocker = await BlockerRepository.find_by_id(blocker_id, db)
        if not blocker:
            return None

        updated = await BlockerRepository.update_status(
            blocker_id,
            status=BlockerStatus.DISMISSED,
            dismissed_reason=reason,
            db=db,
        )
        log.info("blocker.dismissed", id=blocker_id, reason=reason)
        return updated

    @staticmethod
    @llm_retry(max_retries=2)
    async def run_blocker_scan(db) -> list[BlockerCard]:
        """
        Full blocker scan pipeline:
        1. Fetch signals from GitHub + Slack + Monday.com in parallel
        2. Sanitize inputs (guardrails)
        3. Run AI classification via general LLM (Lava → optional Gemini fallback)
        4. Deduplicate against existing active blockers
        5. Stage new blockers in review queue
        6. Persist to MongoDB
        """
        import asyncio

        # Fetch signals in parallel
        pr_data, slack_data, ticket_data = await asyncio.gather(
            GitHubService.get_open_prs_with_age(),
            SlackService.get_recent_messages(hours=48),
            MondayService.get_stale_in_progress_tickets(),
            return_exceptions=True,
        )

        # Sanitize
        if not isinstance(pr_data, Exception):
            pr_data = InputGuardrails.sanitize_github_data(pr_data)
        else:
            log.warning("blocker_scan.github_failed", error=str(pr_data))
            pr_data = {}

        if not isinstance(slack_data, Exception):
            slack_data = InputGuardrails.sanitize_slack_data(slack_data)
        else:
            log.warning("blocker_scan.slack_failed", error=str(slack_data))
            slack_data = []

        if isinstance(ticket_data, Exception):
            log.warning("blocker_scan.monday_failed", error=str(ticket_data))
            ticket_data = []

        team_names = await GitHubService.get_team_members()

        # AI classification
        raw = await call_ai(
            system=Prompts.BLOCKER_SYSTEM,
            user=Prompts.BLOCKER_USER.format(
                timestamp=datetime.now(UTC).isoformat(),
                team_names=", ".join(team_names),
                pr_data=json.dumps(pr_data, indent=2)[:8000],
                slack_data=json.dumps(slack_data, indent=2)[:8000],
                commit_activity=json.dumps(
                    await GitHubService.get_commit_activity_per_engineer(), indent=2
                )[:4000],
                ticket_activity=json.dumps(ticket_data, indent=2)[:4000],
            ),
            task="general",
            temperature=0.1,
        )

        import re
        parsed_raw = re.sub(r"```(?:json)?\s*", "", raw).strip("` \n")
        try:
            result = json.loads(parsed_raw)
            new_blockers_data = result.get("blockers", [])
        except json.JSONDecodeError:
            log.error("blocker_scan.parse_failed", raw=raw[:300])
            return await BlockerRepository.find_active(db)

        # Deduplicate: skip if same engineer + type already active
        existing = await BlockerRepository.find_active(db)
        existing_keys = {(b.engineer, b.type) for b in existing}

        new_blockers = []
        for b_data in new_blockers_data:
            key = (b_data.get("engineer"), b_data.get("type"))
            if key not in existing_keys:
                blocker = BlockerCard(
                    **b_data,
                    status=BlockerStatus.ACTIVE,
                    detected_at=datetime.now(UTC),
                )
                await BlockerRepository.insert(blocker, db)

                # Stage Slack ping in review queue
                await ReviewService.stage_action(
                    action_type="slack_message",
                    title=f"Ping {b_data.get('resolver')} about {b_data.get('engineer')}'s blocker",
                    description=b_data.get("description", ""),
                    data={
                        "channel": f"@{b_data.get('resolver', 'team')}",
                        "message": b_data.get("draft_ping", ""),
                    },
                    reasoning=[f"Blocker detected: {b_data.get('type')}",
                               f"Evidence: {b_data.get('evidence', '')}"],
                    workflow="blocker",
                    db=db,
                )
                new_blockers.append(blocker)

        log.info("blocker_scan.complete",
                 new=len(new_blockers),
                 total_active=len(existing) + len(new_blockers))

        return await BlockerRepository.find_active(db)
```

---

## 11. Repository Pattern

```python
# app/repositories/base.py
"""
Base async repository with common CRUD patterns.
All repos extend this. No business logic here — queries only.
"""

from datetime import datetime, UTC, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import TypeVar, Generic, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    collection_name: str
    model: Type[T]

    @classmethod
    def _col(cls, db: AsyncIOMotorDatabase):
        return db[cls.collection_name]

    @classmethod
    def _to_model(cls, doc: dict) -> T:
        if doc and "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls.model(**doc)

    @classmethod
    async def find_by_id(cls, id: str, db) -> T | None:
        doc = await cls._col(db).find_one({"_id": ObjectId(id)})
        return cls._to_model(doc) if doc else None

    @classmethod
    async def insert(cls, item: T, db) -> T:
        data = item.model_dump(exclude={"id"})
        result = await cls._col(db).insert_one(data)
        return await cls.find_by_id(str(result.inserted_id), db)

    @classmethod
    async def update(cls, id: str, update_data: dict, db) -> T | None:
        update_data["updated_at"] = datetime.now(UTC)
        await cls._col(db).update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data},
        )
        return await cls.find_by_id(id, db)

    @classmethod
    async def delete(cls, id: str, db) -> bool:
        result = await cls._col(db).delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    @classmethod
    async def find_all(cls, db, filter: dict = None, limit: int = 50) -> list[T]:
        cursor = cls._col(db).find(filter or {}).limit(limit).sort("_id", -1)
        return [cls._to_model(doc) async for doc in cursor]

    @classmethod
    async def count(cls, db, filter: dict = None) -> int:
        return await cls._col(db).count_documents(filter or {})


# ── Blocker repository ────────────────────────────────────────────────────────

class BlockerRepository(BaseRepository):
    collection_name = "blockers"
    model = BlockerCard  # imported from models

    @classmethod
    async def find_active(cls, db) -> list:
        return await cls.find_all(db, filter={"status": "active"})

    @classmethod
    async def find_resolved(cls, days: int, db) -> list:
        since = datetime.now(UTC) - timedelta(days=days)
        return await cls.find_all(
            db,
            filter={"status": {"$in": ["resolved", "dismissed"]},
                    "detected_at": {"$gte": since}},
        )

    @classmethod
    async def update_status(cls, id: str, status: str,
                            dismissed_reason: str | None, db):
        return await cls.update(id, {
            "status": status,
            "dismissed_reason": dismissed_reason,
            "resolved_at": datetime.now(UTC),
        }, db)


# ── Review queue repository ───────────────────────────────────────────────────

class ReviewRepository(BaseRepository):
    collection_name = "review_queue"
    model = ReviewAction  # imported from models

    @classmethod
    async def find_pending(cls, db) -> list:
        return await cls.find_all(db, filter={"status": "pending"})

    @classmethod
    async def find_by_workflow(cls, workflow: str, db) -> list:
        return await cls.find_all(db, filter={
            "workflow": workflow,
            "status": "pending",
        })

    @classmethod
    async def count_pending(cls, db) -> int:
        return await cls.count(db, filter={"status": "pending"})
```

---

## 12. Pydantic Models

```python
# app/models/common.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")


class APIResponse(BaseModel):
    success: bool
    message: str = ""
    data: dict | None = None


# app/models/auth.py
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# app/models/blocker.py
from enum import Enum
from datetime import datetime

class BlockerSeverity(str, Enum):
    CRITICAL = "critical"
    MEDIUM = "medium"
    WATCH = "watch"

class BlockerStatus(str, Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"

class BlockerType(str, Enum):
    PR_STALE = "pr_stale"
    SLACK_SIGNAL = "slack_signal"
    INACTIVITY = "inactivity"
    DEPENDENCY_MISSING = "dependency_missing"

class BlockerCard(BaseModel):
    id: str | None = None
    engineer: str
    severity: BlockerSeverity
    type: BlockerType
    description: str
    blocked_for: str
    evidence: str
    resolver: str
    draft_ping: str
    status: BlockerStatus = BlockerStatus.ACTIVE
    detected_at: datetime = Field(default_factory=lambda: datetime.now())
    dismissed_reason: str | None = None
    resolved_at: datetime | None = None

class DismissRequest(BaseModel):
    reason: str | None = None


# app/models/review.py
class ActionType(str, Enum):
    SLACK_MESSAGE = "slack_message"
    MONDAY_BOARD = "monday_board"
    CALENDAR_EVENT = "calendar_event"
    GMAIL_SEND = "gmail_send"
    MONDAY_SPRINT = "monday_sprint"

class ActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class ReviewAction(BaseModel):
    id: str | None = None
    type: ActionType
    title: str
    description: str
    data: dict
    reasoning: list[str] = []
    workflow: str
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    edited_content: dict | None = None
    rejected_reason: str | None = None
    execution_result: dict | None = None

class BatchApproveRequest(BaseModel):
    action_ids: list[str]

class RejectRequest(BaseModel):
    reason: str | None = None

class EditActionRequest(BaseModel):
    content: dict  # partial update to action.data
```

---

## 13. Error Handling Pattern

```python
# Pattern: service raises → router catches → returns structured error

# ── In service layer (raise, never catch) ────────────────────────────────────
class SprintService:
    @staticmethod
    async def approve_sprint(sprint_id: str, db) -> dict:
        draft = await SprintRepository.find_draft(db)
        if not draft:
            raise ValueError("No sprint draft found. Generate a draft first.")

        if draft.utilization_pct > 110:
            raise ValueError(
                f"Sprint is at {draft.utilization_pct}% capacity — over limit. "
                f"Deselect some tickets before approving."
            )
        # proceed with approval...

# ── In router (catch ValueError → 400, Exception → 500) ─────────────────────
@router.post("/approve")
async def approve_sprint(
    current_user=Depends(get_current_user),
    db=Depends(get_db_dep),
):
    try:
        result = await SprintService.approve_sprint(db=db)
        return result
    except ValueError as e:
        # Known business error — 400 with message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unknown error — 500, log it
        log.error("sprint.approve_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Sprint approval failed. Please try again."
        )

# ── Global handler in main.py catches anything that slips through ────────────
# See Section 3 — global_exception_handler
```

---

## 14. Middleware Stack

```python
# app/middleware.py
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

log = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID into every request + response."""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, latency."""
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        # Skip health check spam
        if request.url.path != "/health":
            log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                latency_ms=latency_ms,
                request_id=getattr(request.state, "request_id", "—"),
            )
        return response
```

```python
# Middleware order in main.py (outermost wraps everything):
# 1. CORSMiddleware      — handle preflight before anything else
# 2. LoggingMiddleware   — log after CORS but before request ID
# 3. RequestIDMiddleware — innermost, so request_id available in logs

# Rate limiting via slowapi (applied per-route, not middleware):
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

# Apply to specific routes:
@router.post("/generate")
@limiter.limit("10/minute")   # sprint generation is expensive
async def generate_sprint(request: Request, ...):
    ...

@router.post("/scan")
@limiter.limit("20/minute")   # blocker scan hits multiple APIs
async def scan_blockers(request: Request, ...):
    ...
```

---

## 15. Background Jobs (APScheduler)

```python
# app/jobs/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import structlog

log = structlog.get_logger()
scheduler = AsyncIOScheduler(timezone="America/New_York")


async def start_scheduler():
    from app.jobs.standup_job import run_standup_job
    from app.jobs.blocker_job import run_blocker_job
    from app.jobs.context_job import run_context_job
    from app.jobs.report_job import run_report_job

    # Context refresh — every 15 minutes
    scheduler.add_job(
        run_context_job,
        IntervalTrigger(minutes=15),
        id="context_refresh",
        name="Refresh project context snapshot",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Standup digest — every day at 9:00am ET
    scheduler.add_job(
        run_standup_job,
        CronTrigger(hour=9, minute=0, timezone="America/New_York"),
        id="daily_standup",
        name="Generate daily standup digest",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Blocker scan — every 15 minutes during work hours (8am–8pm ET)
    scheduler.add_job(
        run_blocker_job,
        CronTrigger(hour="8-20", minute="*/15", timezone="America/New_York"),
        id="blocker_poll",
        name="Scan for new blockers",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Status report — every Friday at 5:00pm ET
    scheduler.add_job(
        run_report_job,
        CronTrigger(day_of_week="fri", hour=17, minute=0,
                    timezone="America/New_York"),
        id="weekly_report",
        name="Generate Friday status report",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    log.info("scheduler.started", jobs=len(scheduler.get_jobs()))


async def stop_scheduler():
    scheduler.shutdown(wait=False)
    log.info("scheduler.stopped")
```

```python
# app/jobs/standup_job.py
"""Daily standup digest background job."""

from app.db.mongo import get_db
from app.services.standup_service import StandupService
import structlog

log = structlog.get_logger()


async def run_standup_job():
    log.info("job.standup.start")
    try:
        db = get_db()
        digest = await StandupService.generate_digest(db)
        log.info("job.standup.complete",
                 engineers=len(digest.get("digest", [])))
    except Exception as e:
        log.error("job.standup.failed", error=str(e))
```

```python
# app/jobs/context_job.py
"""Context snapshot refresh job."""

from app.services.context_builder import build_context_snapshot
import structlog

log = structlog.get_logger()


async def run_context_job():
    try:
        snapshot = await build_context_snapshot()
        sources = snapshot.get("sources_available", {})
        log.info("job.context.refreshed", sources=sources)
    except Exception as e:
        log.error("job.context.failed", error=str(e))
```

---

## 16. Structured Logging

```python
# app/lib/logging_config.py
"""
structlog JSON logging setup.
Call configure_logging() before app creation in main.py.
"""

import logging
import sys
import structlog


def configure_logging(log_level: str = "INFO"):
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Quiet noisy libraries
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

```python
# Example log output (JSON):
{
  "event": "http.request",
  "method": "POST",
  "path": "/api/v1/sprint/approve",
  "status": 200,
  "latency_ms": 847.2,
  "request_id": "a3f7c2b1",
  "timestamp": "2026-03-28T14:32:11.427Z",
  "level": "info"
}

{
  "event": "blocker_scan.complete",
  "new": 2,
  "total_active": 3,
  "timestamp": "2026-03-28T14:33:00.001Z",
  "level": "info"
}

{
  "event": "llm.cost",
  "model": "gpt-4o-mini",
  "input_tokens": 1842,
  "output_tokens": 312,
  "cost_usd": 0.000007,
  "session_total_usd": 0.0031,
  "timestamp": "2026-03-28T14:33:02.118Z",
  "level": "info"
}
```

---

## 17. Twilio Webhook Handler (Voice Agent)

```python
# app/api/v1/voice.py
"""
Twilio inbound call webhook.
ElevenLabs Conversational AI handles the actual conversation.
This endpoint: accepts call → returns TwiML → bridges to ElevenLabs.
"""

from fastapi import APIRouter, Request, Response, Depends
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from app.services.voice_service import VoiceService
from app.db.mongo import get_db_dep
from app.dependencies import get_current_user
import structlog

log = structlog.get_logger()
router = APIRouter()


@router.post("/webhook/inbound")
async def inbound_call(request: Request, db=Depends(get_db_dep)):
    """
    Twilio calls this when someone dials our number.
    Returns TwiML that connects the call to ElevenLabs Conversational AI.
    The ElevenLabs agent is pre-configured with our agent_id in the dashboard.
    """
    form = await request.form()
    caller = form.get("From", "unknown")
    call_sid = form.get("CallSid", "")

    log.info("voice.inbound_call", caller=caller, call_sid=call_sid)

    # Get fresh context for the voice agent
    context = await VoiceService.get_voice_context(db)

    # Log the call start
    await VoiceService.log_call_start(call_sid, caller, db)

    # Build TwiML to connect to ElevenLabs
    twiml = VoiceResponse()
    connect = Connect()
    # ElevenLabs Conversational AI WebSocket stream
    stream = Stream(url=f"wss://api.elevenlabs.io/v1/convai/call?agent_id={context['agent_id']}")
    stream.parameter(name="agent_context", value=context["system_prompt"])
    connect.append(stream)
    twiml.append(connect)

    return Response(content=str(twiml), media_type="application/xml")


@router.get("/context")
async def get_voice_context(
    current_user=Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get the current context the voice agent has access to."""
    return await VoiceService.get_voice_context_summary(db)


@router.get("/transcripts")
async def get_transcripts(
    limit: int = 10,
    current_user=Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Get last N call transcripts."""
    return await VoiceService.get_transcripts(limit=limit, db=db)
```

---

## 18. Environment Variables (`.env.example`)

```bash
# ── App ───────────────────────────────────────────────────────────────────────
ENV=development

# ── Auth (hardcoded demo user) ────────────────────────────────────────────────
DEMO_EMAIL=pm@pilotpm.demo
DEMO_PASSWORD=pilotpm2026
JWT_SECRET=change-this-in-production-use-openssl-rand-hex-32
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB=pilotpm

# ── AI — Lava forward (see https://lava.so/docs/get-started/quickstart-track.md) ─
LAVA_API_KEY=...
LAVA_BASE=https://api.lava.so
# LAVA_FORWARD_UPSTREAM=https://api.openai.com/v1/chat/completions
# LAVA_MODEL_PRIMARY=gpt-4o-mini
# LAVA_MODEL_FALLBACK=gpt-4o
# GEMINI_API_KEY=                          # optional — last resort if Lava fails
# GEMINI_MODEL=gemini-3-flash-preview

# ── K2 Think V2 — MBZUAI sponsor, direct ─────────────────────────────────────
K2_API_KEY=...
K2_API_BASE=https://api.k2think.ai

# ── GitHub ────────────────────────────────────────────────────────────────────
GITHUB_TOKEN=ghp_...

# ── Slack ─────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN=xoxb-...

# ── Monday.com ────────────────────────────────────────────────────────────────
MONDAY_API_KEY=...

# ── Voice ─────────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE=+12035550000

# ── Analytics ─────────────────────────────────────────────────────────────────
HEX_API_KEY=...

# ── Stakeholders ─────────────────────────────────────────────────────────────
STAKEHOLDER_EMAILS=founder@startup.com,investor@vc.com
```

---

## 19. Requirements

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.0
pydantic-settings==2.6.0

# MongoDB
motor==3.6.0
pymongo==4.9.0

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# HTTP client (API integrations)
httpx==0.27.0

# AI / Agents — all cloud calls via Lava (OpenAI-compatible REST)
langchain==0.3.0
langgraph==0.2.0

# Scheduling
apscheduler==3.10.4

# Voice
twilio==9.3.0

# Rate limiting
slowapi==0.1.9

# Logging
structlog==24.4.0

# Utilities
python-multipart==0.0.12    # form data (Twilio webhook)
python-dotenv==1.0.1
```

---

## 20. Startup Sequence (Build Order Tonight)

```
1. app/config.py              ← Settings, load .env
2. app/db/mongo.py            ← Motor client, connect_mongo()
3. app/db/indexes.py          ← MongoDB indexes
4. app/lib/logging_config.py  ← structlog setup
5. app/lib/llm.py             ← AI router (Lava + K2 + fallback)
6. app/lib/prompts.py         ← All prompts
7. app/lib/retry.py           ← llm_retry decorator
8. app/models/*.py            ← Pydantic models
9. app/repositories/*.py      ← MongoDB queries
10. app/integrations/*.py     ← GitHub, Slack, Monday.com calls
11. app/services/context_builder.py  ← Shared context snapshot
12. app/services/auth_service.py     ← JWT
13. app/services/*.py         ← One per workflow
14. app/jobs/*.py             ← APScheduler jobs
15. app/api/v1/*.py           ← Route handlers
16. app/main.py               ← App factory, wire everything
17. uvicorn app.main:app      ← Run it
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | March 28, 2026 | Aman | Initial — all sections, PilotPM-specific |
