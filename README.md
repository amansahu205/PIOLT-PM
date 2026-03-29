<div align="center">

<img src="frontend/public/logo.png" alt="PilotPM Logo" width="120" />

# PilotPM

### Your engineering team's AI pilot — no standups, no missed blockers, no manual reports.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-4ea94b?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-orange?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Lava](https://img.shields.io/badge/Lava-Gateway-blueviolet?style=flat)](https://lava.so/)
[![K2 Think V2](https://img.shields.io/badge/K2_Think-V2-red?style=flat)](https://k2think.ai/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-000000?style=flat)](https://elevenlabs.io/)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=flat&logo=twilio&logoColor=white)](https://www.twilio.com/)
[![Hex](https://img.shields.io/badge/Hex-Analytics-5A67D8?style=flat)](https://hex.tech/)
[![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)](https://slack.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deploy-black?style=flat&logo=vercel&logoColor=white)](https://vercel.com/)

**[Live Demo](https://www.iloveyhacks.biz) · Built for Y-Hack 2026**

</div>

---

## What is PilotPM?

Software PMs at early-stage startups spend **60%+ of their time on coordination** — standups, status updates, blocker follow-ups, sprint planning — work that produces zero direct product value.

PilotPM is an **AI-powered project management orchestrator** that watches GitHub, Slack, and Monday.com continuously and acts as a tireless chief of staff. Every morning your standup is already done. Blockers surface before engineers report them. Sprint planning takes 5 minutes. Your Friday stakeholder email writes and sends itself. And when you're away from your desk — you call a real phone number and ask your AI agent about the project.

The PM stays in control: **every AI action lands in a review queue for approval before anything executes.**

---

## Core Features

| Feature | What it does |
|---------|-------------|
| **Async Standup Digest** | Scans GitHub commits, PRs, and Slack messages every morning. Generates a per-engineer summary — what they shipped, what they're on, and whether they're blocked — no meeting required. |
| **Blocker Radar** | Detects blockers automatically: stale PRs (48h+), Slack messages with blocking language, engineers with no commits in 24h. Surfaces each with a pre-drafted resolution ping. |
| **Sprint Autopilot** | Pulls Monday.com backlog, scores every ticket via K2 Think V2 (impact × effort), calculates per-engineer velocity, and presents a capacity-checked draft sprint for one-click approval. |
| **Auto Status Reports** | Compiles shipped tickets, merged PRs, resolved blockers, and next-week priorities into a stakeholder email with a Hex analytics dashboard. Sends on Friday — automatically. |
| **Voice Agent** | Call a real Twilio phone number. Ask "What's blocking my team?" or "Give me the sprint summary." An ElevenLabs AI voice answers from live data in under 3 seconds. Say "send an email" or "schedule a meeting" — it executes on the call. |
| **Human Review Queue** | Every agent-proposed action (Slack ping, Monday update, email send) is staged here first. PM approves, edits, or rejects before anything hits the outside world. |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                         │
│   GitHub API    ·    Slack API    ·    Monday.com API   │
└────────────────────────┬────────────────────────────────┘
                         │  parallel fetch every 15 min
                         ▼
┌─────────────────────────────────────────────────────────┐
│               CONTEXT BUILDER (MongoDB)                 │
│       Project snapshot · refreshed · TTL-aware         │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│             LANGGRAPH ORCHESTRATOR                      │
│                                                         │
│  ┌──────────┐ ┌─────────┐ ┌────────┐ ┌────────────┐   │
│  │ Standup  │ │ Blocker │ │ Sprint │ │  Reports   │   │
│  │  Agent   │ │  Agent  │ │ Agent  │ │   Agent    │   │
│  └────┬─────┘ └────┬────┘ └───┬────┘ └─────┬──────┘   │
└───────┼─────────────┼──────────┼────────────┼──────────┘
        └─────────────┴──────────┴────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  REVIEW QUEUE                           │
│          PM approves / edits / rejects                 │
└────────────────────────┬────────────────────────────────┘
                         │ on approval
                         ▼
              Slack · Monday.com · Gmail · Calendar

                         +

┌─────────────────────────────────────────────────────────┐
│                   VOICE AGENT                           │
│  Twilio inbound → ElevenLabs ConvAI → live context     │
│  Tools: send_email · schedule_meeting (mid-call)       │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| Framework | FastAPI | 0.135 | Async-native, auto OpenAPI docs, Pydantic built-in |
| Runtime | Python | 3.11 | Best-in-class async + AI/ML ecosystem |
| Server | Uvicorn | latest | Production ASGI server |
| Database driver | Motor (async MongoDB) | 3.7 | Non-blocking queries match FastAPI's async model |
| Database | MongoDB Atlas | — | Document-shaped data, free tier, zero migrations |
| Agent orchestration | LangGraph | 1.1 | Directed agent graph with conditional edges per workflow |
| Background jobs | APScheduler | 3.11 | In-process cron — no Redis, no Celery, no extra infra |
| Validation | Pydantic v2 | 2.12 | Runtime validation + settings management |
| Auth | python-jose (JWT) | 3.5 | Stateless, demo-ready |
| Rate limiting | slowapi | 0.1 | Per-IP throttle with one decorator |
| Logging | structlog | 25.5 | JSON-structured, correlates with agent reasoning traces |
| Package manager | uv | latest | 10× faster than pip, reproducible lockfile |

### AI & Models

| Model / Service | Provider | Route | Used For |
|----------------|---------|-------|---------|
| `gpt-4o-mini` | OpenAI | **Lava forward proxy** | Primary LLM — standup, blockers, reports, classify |
| `gpt-4o` | OpenAI | **Lava forward proxy** | Fallback if primary model errors |
| `MBZUAI-IFM/K2-Think-v2` | MBZUAI | Direct (`api.k2think.ai`) | Sprint planning + backlog scoring (multi-step reasoning) |
| Gemini (configurable) | Google | `google-genai` SDK | Last-resort fallback if both Lava calls fail |
| Conversational AI | ElevenLabs | WebSocket + Twilio | Voice agent — STT · dialogue · TTS loop |

**Model routing:**

```
call_ai(task)
  ├── task = "sprint" / "backlog"  →  K2 Think V2  →  (fail) → Lava chain
  └── everything else
        ├── Lava: LAVA_MODEL_PRIMARY  (gpt-4o-mini)
        ├── Lava: LAVA_MODEL_FALLBACK (gpt-4o)
        └── Gemini direct            (only if GEMINI_API_KEY set + both Lava calls failed)
```

### Integrations

| Service | Protocol | Used For |
|---------|---------|---------|
| **GitHub** | REST API | Commits, open PRs, PR ages, team members, velocity |
| **Slack** | Web API | Read channel messages, post digests, send blocker DMs |
| **Monday.com** | GraphQL API | Sprint boards, backlog tickets, ticket status updates |
| **ElevenLabs** | `register-call` + WebSocket | Voice agent STT/TTS + mid-call tool execution |
| **Twilio** | Webhook + TwiML | Real phone number, inbound call routing |
| **Gmail / SMTP** | SMTP | Stakeholder emails, calendar invite fallback |
| **Google Calendar** | REST API + service account | Meeting creation from voice calls |
| **Hex** | Embed API | Sprint analytics dashboards in weekly reports |

### Frontend

| Technology | Version | Why |
|-----------|---------|-----|
| Next.js (App Router) | 16 | File-based routing, RSC, zero-config Vercel deploy |
| React | 19 | Component model, concurrent features |
| Tailwind CSS | 3 | Utility-first, consistent dark theme |
| shadcn/ui | — | Accessible component primitives, zero design time |
| Framer Motion | — | Smooth entrance animations, card transitions |
| Lucide React | — | Consistent icon system, tree-shakeable |
| pnpm | — | Fast installs, disk-efficient |
| Vercel | — | Zero-config deploy, edge CDN, custom domain |

---

## Repository Layout

```
PIOLT-PM/
├── app/                        # FastAPI backend
│   ├── api/v1/                 # HTTP routers
│   │   ├── auth.py
│   │   ├── standup.py          # F-001 standup digest
│   │   ├── blockers.py         # F-002 blocker radar
│   │   ├── sprint.py           # F-003 sprint autopilot
│   │   ├── reports.py          # F-004 status reports
│   │   ├── voice.py            # F-005 voice agent + Twilio webhook
│   │   ├── voice_tools.py      # ElevenLabs tool webhooks (email + calendar)
│   │   ├── backlog.py          # F-010 backlog prioritizer
│   │   ├── review.py           # F-011 human review queue
│   │   └── health.py
│   ├── integrations/
│   │   ├── github_service.py
│   │   ├── slack_service.py
│   │   ├── monday_service.py
│   │   ├── gmail_service.py
│   │   ├── calendar_service.py # Google Calendar API + ICS fallback
│   │   ├── elevenlabs_service.py
│   │   ├── twilio_service.py
│   │   └── hex_service.py
│   ├── services/
│   │   ├── context_builder.py  # Shared project snapshot (15-min cache)
│   │   ├── standup_service.py
│   │   ├── blocker_service.py
│   │   ├── sprint_service.py
│   │   ├── report_service.py
│   │   ├── voice_service.py
│   │   ├── backlog_service.py
│   │   ├── review_service.py   # Review queue + action staging
│   │   └── orchestrator.py     # LangGraph workflow graph
│   ├── repositories/           # MongoDB queries only
│   ├── models/                 # Pydantic schemas
│   ├── jobs/
│   │   ├── scheduler.py        # APScheduler setup
│   │   ├── context_job.py      # Every 15 min
│   │   ├── standup_job.py      # Daily 09:00 ET
│   │   ├── blocker_job.py      # Every 15 min, 08:00–20:00 ET
│   │   └── report_job.py       # Friday 17:00 ET
│   ├── lib/
│   │   ├── llm.py              # call_ai() — Lava → K2 → Gemini routing
│   │   ├── prompts.py          # All system + user prompts
│   │   ├── guardrails.py       # Output validation
│   │   ├── retry.py            # LLM retry decorator
│   │   └── cost.py             # Token usage tracking
│   ├── db/                     # Motor connection + index setup
│   ├── config.py               # Pydantic Settings (all env vars)
│   ├── dependencies.py         # FastAPI dependencies (JWT, DB)
│   ├── middleware.py           # Request ID, logging, CORS
│   └── main.py                 # App factory + lifespan
│
├── frontend/                   # Next.js 16 dashboard + landing page
│   ├── app/
│   │   ├── page.tsx            # Landing page (immersive scroll)
│   │   ├── login/page.tsx
│   │   └── dashboard/
│   │       ├── page.tsx        # Overview: standup digest + stats
│   │       ├── standup/        # Full standup feed
│   │       ├── blockers/       # Blocker radar cards
│   │       ├── sprint/         # Sprint planner
│   │       ├── reports/        # Status report composer
│   │       ├── voice/          # Voice agent + call log
│   │       └── review/         # Human review queue
│   ├── components/
│   │   ├── sidebar.tsx
│   │   ├── navbar.tsx
│   │   └── ui/                 # shadcn/ui primitives
│   ├── lib/
│   │   ├── api.ts              # Typed fetch wrapper
│   │   └── auth.ts             # JWT localStorage helpers
│   └── public/
│       └── logo.png            # Brand logo
│
├── docs/
│   ├── PRD.md                  # Full product requirements
│   ├── IMPLEMENTATION_PLAN.md  # 24-hour build roadmap
│   ├── AI_ARCHITECTURE.md      # AI/model design
│   ├── BACKEND_STRUCTURE.md    # Backend architecture
│   └── APP_FLOW.md             # Screen flows + auth
│
├── pyproject.toml              # uv dependencies
├── uv.lock
├── .env.example
└── README.md
```

---

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js 20+** and **pnpm** — `corepack enable && corepack prepare pnpm@latest --activate`
- **MongoDB** — [Atlas free tier](https://www.mongodb.com/atlas) or local instance
- API keys for the integrations you need (see [Configuration](#configuration))

---

## Configuration

Copy `.env.example` to `.env` at the repository root:

```bash
cp .env.example .env
```

### Required — backend will not start without these

| Variable | Purpose |
|----------|---------|
| `DEMO_EMAIL` | Demo PM login email |
| `DEMO_PASSWORD` | Demo PM login password |
| `JWT_SECRET` | Secret for signing JWTs (`openssl rand -hex 32`) |
| `MONGODB_URI` | MongoDB Atlas or local connection string |
| `LAVA_API_KEY` | Lava gateway key (also accepted as `LAVA_SECRET_KEY`) |
| `K2_API_KEY` | MBZUAI K2 Think V2 key |
| `GITHUB_TOKEN` | GitHub fine-grained or classic PAT |
| `GITHUB_REPO` | Target repo in `owner/repo` format |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-…`) |
| `MONDAY_API_KEY` | Monday.com API token |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_AGENT_ID` | ConvAI agent ID (must have telephony / Twilio enabled) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE` | Your Twilio number in E.164 format (e.g. `+15551234567`) |
| `HEX_API_KEY` | Hex analytics API key |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `SLACK_ENGINEERING_CHANNEL` | `#engineering` | Channel for message reads + blocker pings |
| `SLACK_STANDUP_CHANNEL` | `#standup-digest` | Target channel for staged standup digests |
| `STAKEHOLDER_EMAILS` | — | Comma-separated recipients for reports + voice-triggered emails |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | — | SMTP credentials for outbound email |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | — | Full service account JSON (or base64) for Google Calendar API |
| `GOOGLE_CALENDAR_ID` | `primary` | Calendar to create events on |
| `ELEVENLABS_TOOL_SECRET` | — | HMAC secret for verifying ElevenLabs tool webhooks |
| `GEMINI_API_KEY` | — | Google Gemini — last-resort LLM fallback only |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Override to pin a Gemini model |
| `LAVA_MODEL_PRIMARY` | `gpt-4o-mini` | Primary model sent through Lava |
| `LAVA_MODEL_FALLBACK` | `gpt-4o` | Fallback if primary errors |
| `MONDAY_BOARD_ID` | — | Monday board ID — unset uses seeded demo data |
| `CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000"]` | JSON array of allowed browser origins |

### Frontend (`frontend/.env.local`)

```bash
cp frontend/.env.local.example frontend/.env.local
```

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend base URL, no trailing slash — e.g. `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_TWILIO_PHONE` | Optional — displayed on the Voice dashboard page |

> **Port conflict:** If `8000` is taken, start the API on `--port 8001` and update `NEXT_PUBLIC_API_URL` to match.

---

## Running Locally

### 1 — Backend

```bash
# From repository root
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Wait for `Application startup complete`. Then verify:

- **Interactive docs:** `http://127.0.0.1:8000/docs`
- **Health check:** `GET http://127.0.0.1:8000/health`

### 2 — Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`. Sign in with `DEMO_EMAIL` / `DEMO_PASSWORD` from your `.env`.

> JWT is stored in `localStorage` (`pilotpm_token`). API calls send `Authorization: Bearer …`.

---

## Deployment

### Backend — Railway

1. Create a new Railway service from this GitHub repo.
2. Set all required environment variables in the Railway UI.
3. **Start command** (auto-detected via `railpack.json`):
   ```
   uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. **MongoDB Atlas → Network Access:** Add `0.0.0.0/0` for demo environments, or use [Railway static egress IPs](https://docs.railway.com/reference/static-outbound-ip) for production.
5. Verify: `GET https://<your-api>.up.railway.app/health`

### Frontend — Vercel

1. **Vercel Dashboard → Add New → Project** — import this repo.
2. Set **Root Directory** to `frontend`.
3. Add environment variables for Production:

   | Variable | Value |
   |----------|-------|
   | `NEXT_PUBLIC_API_URL` | `https://<your-api>.up.railway.app` — no trailing slash |
   | `NEXT_PUBLIC_TWILIO_PHONE` | Your Twilio number (optional) |

4. Deploy. Note your domain (`https://www.iloveyhacks.biz`).
5. **Update CORS on Railway** — set `CORS_ORIGINS`:

   ```json
   ["https://www.iloveyhacks.biz","http://localhost:3000","http://127.0.0.1:3000"]
   ```

   Redeploy the API after changing `CORS_ORIGINS`.

### Twilio — Voice Webhook

Twilio POSTs to your **API** (not Vercel). Requires a live public HTTPS URL.

1. **Twilio Console → Phone Numbers → Manage → Active Numbers** → select your number.
2. Under **Voice & Fax → A call comes in**: set **Webhook**, **HTTP POST**.
3. URL:
   ```
   https://<your-api>.up.railway.app/api/v1/voice/webhook/inbound
   ```
4. Save. Test by dialing your Twilio number — check Railway logs for `voice.elevenlabs_register_ok`.

> **Trial accounts:** Twilio may POST the webhook twice per call (trial disclaimer + key press). PilotPM caches TwiML by `CallSid` for 3 minutes so ElevenLabs `register-call` is only invoked once per call leg. Upgrade your Twilio account to remove the trial prompt for demos.

### ElevenLabs Voice Tools

Configure two **Server Tools** in the ElevenLabs dashboard under your ConvAI agent:

**`send_email`**

| Field | Value |
|-------|-------|
| Name | `send_email` |
| Description | Send an email on behalf of the PM when the caller asks to send a message, status update, or notification. |
| URL | `https://<your-api>.up.railway.app/api/v1/voice/tools/send_email` |
| Parameters | `recipient_email` (string, required) · `subject` (string, required) · `body` (string, required) |

**`schedule_meeting`**

| Field | Value |
|-------|-------|
| Name | `schedule_meeting` |
| Description | Schedule a calendar event when the caller asks to book, schedule, or set up a meeting or call. |
| URL | `https://<your-api>.up.railway.app/api/v1/voice/tools/schedule_meeting` |
| Parameters | `title` (string, required) · `start_time` (string, ISO8601) · `duration_minutes` (integer, default 30) · `attendees` (array of strings) · `description` (string) |

> If `GOOGLE_SERVICE_ACCOUNT_JSON` is not configured, `schedule_meeting` sends a standard ICS calendar invite via SMTP.

> In the agent's system prompt, reference `{{pilotpm_context}}` as a dynamic variable so the agent reads PilotPM's live project context on every call.

---

## API Reference

All `/api/v1/*` routes require `Authorization: Bearer <token>`. Obtain a token via `POST /auth/login`.

| Area | Route | Method | Description |
|------|-------|--------|-------------|
| **Auth** | `/auth/login` | POST | Exchange credentials for JWT |
| **Health** | `/health` | GET | Service health + MongoDB status |
| **Standup** | `/api/v1/standup/today` | GET | Today's digest (auto-generates if missing) |
| | `/api/v1/standup/generate` | POST | Force-regenerate digest from live data |
| | `/api/v1/standup/history` | GET | Last 7 digests |
| **Blockers** | `/api/v1/blockers` | GET | All active blocker cards |
| | `/api/v1/blockers/scan` | POST | Trigger immediate blocker scan |
| | `/api/v1/blockers/{id}/dismiss` | PATCH | Dismiss a blocker card |
| **Sprint** | `/api/v1/sprint/current` | GET | Live sprint board snapshot |
| | `/api/v1/sprint/draft` | GET | Current draft sprint plan |
| | `/api/v1/sprint/draft/generate` | POST | Generate new AI-scored draft |
| | `/api/v1/sprint/draft/tickets` | PATCH | Toggle ticket inclusion / reassign engineer |
| | `/api/v1/sprint/approve` | POST | Approve draft → push to Monday.com |
| **Reports** | `/api/v1/reports/current` | GET | Latest report |
| | `/api/v1/reports/generate` | POST | Generate weekly report |
| | `/api/v1/reports/{id}/edit` | PATCH | Edit report body before sending |
| | `/api/v1/reports/{id}/send` | POST | Stage report email for approval |
| **Voice** | `/api/v1/voice/webhook/inbound` | POST | Twilio inbound call webhook (no auth required) |
| | `/api/v1/voice/context` | GET | Live context summary fed to voice agent |
| | `/api/v1/voice/transcripts` | GET | Recent call log |
| | `/api/v1/voice/tools/send_email` | POST | ElevenLabs tool webhook — send email mid-call |
| | `/api/v1/voice/tools/schedule_meeting` | POST | ElevenLabs tool webhook — create calendar event mid-call |
| **Backlog** | `/api/v1/backlog` | GET | Scored + ranked backlog |
| | `/api/v1/backlog/score` | POST | Re-score backlog with K2 Think V2 |
| **Review** | `/api/v1/review` | GET | Pending review queue items |
| | `/api/v1/review/{id}/approve` | POST | Approve and execute action |
| | `/api/v1/review/{id}/reject` | POST | Reject with optional reason (logged for improvement) |

---

## Scheduled Jobs

All times **America/New_York**.

| Job ID | Schedule | What it does |
|--------|----------|-------------|
| `context_refresh` | Every **15 minutes** | Fetches fresh data from GitHub + Slack + Monday.com, stores snapshot in MongoDB |
| `daily_standup` | **09:00** daily | Generates standup digest + stages Slack post to review queue |
| `blocker_poll` | Every **15 min**, 08:00–20:00 | Scans for new blockers + stages Slack pings |
| `weekly_report` | **Friday 17:00** | Generates weekly status report draft |

On startup, the app immediately warms the context snapshot — no waiting for the first tick.

---

## Agentic Workflows

### Shared Context Layer

Every agent reads from a cached MongoDB snapshot — no agent calls integrations directly.

```
context_builder.build_context_snapshot()
  ├── GitHubService.get_recent_activity(hours=24)
  ├── SlackService.get_recent_messages(hours=48)
  └── MondayService.get_sprint_status()
        │
        ▼
  MongoDB: project_context  (TTL: 15 min)
```

### Human-in-the-Loop

No agent writes to the outside world directly. Every proposed action goes through:

```python
review_service.stage_action(
    action_type="slack_message",   # or: monday_sprint / gmail_send / calendar_events
    title="...",
    data={...},
    reasoning="...",               # agent's reasoning — shown in dashboard
    workflow="standup",
)
```

This inserts a `pending` document into `review_queue`. The Review Queue dashboard lists all pending items with the agent's reasoning trail. `POST /review/{id}/approve` executes the action; `POST .../reject` logs the reason.

### Standup Agent

```
Context snapshot (GitHub + Slack + Monday)
  → LLM (Lava / gpt-4o-mini)
  → JSON: per-engineer {status, did, working_on, blocker, sources}
  → MongoDB: standup_repo
  → Review queue: staged Slack post to #standup-digest
```

**Triggers:** `POST /api/v1/standup/generate` (manual) · cron 09:00 ET daily

### Blocker Agent

```
Open PRs (age) + Slack messages (48h) + stale Monday tickets + commit gaps
  → LLM (Lava / gpt-4o-mini)
  → JSON: [{who, what, since, draft_ping}]
  → MongoDB: blocker_repo (deduplicated)
  → Review queue: one staged Slack ping per new blocker
```

**Triggers:** `POST /api/v1/blockers/scan` (manual) · cron every 15 min, 08:00–20:00 ET

### Sprint Agent

```
Monday backlog + GitHub velocity
  → K2 Think V2 (MBZUAI)          ← sponsor model for multi-step reasoning
  → Scored tickets (1–100) + reasoning note per ticket
  → Capacity-check (≤ 110% velocity)
  → MongoDB: sprint_draft_repo
  → On approval → Review queue: monday_sprint + calendar_events
```

**Triggers:** `POST /api/v1/sprint/draft/generate` (manual)

### Report Agent

```
Context + merged PRs (7d) + resolved blockers + Monday tickets
  → LLM (Lava / gpt-4o-mini)
  → Subject + body + optional Hex analytics embed URL
  → MongoDB: report_repo
  → On send → Review queue: gmail_send to STAKEHOLDER_EMAILS
```

**Triggers:** `POST /api/v1/reports/generate` (manual) · cron Friday 17:00 ET

### Voice Agent

```
Inbound call → Twilio POST /api/v1/voice/webhook/inbound
  → VoiceService builds system prompt from live context snapshot
  → ElevenLabs register-call API  (injects pilotpm_context as dynamic variable)
  → TwiML returned to Twilio      (WebSocket stream opened to ElevenLabs)
  → ElevenLabs ConvAI answers questions from live data

  During call — tool execution:
    "Send a status update to the team"
      → POST /api/v1/voice/tools/send_email
      → GmailService.send_email()
      → Agent speaks: "Done, email sent."

    "Schedule sprint planning for Friday at 2pm"
      → POST /api/v1/voice/tools/schedule_meeting
      → CalendarService.create_event()   (Google Calendar API or ICS fallback)
      → Agent speaks: "Meeting created for Friday at 2pm UTC."
```

---

## Sponsor Prize Mapping

| Sponsor | Track | Integration | Feature |
|---------|-------|-------------|---------|
| **Harper** | Personal AI Agents in Enterprises | Full agentic stack | All 5 P0 workflows |
| **Lava** | API Gateway | Lava forward proxy | Every general LLM call routes through Lava |
| **MBZUAI** | K2 Think V2 | Direct API | Sprint planning + backlog scoring |
| **Hex** | Analytics API | Hex embed API | Sprint dashboards in weekly reports |
| **ElevenLabs (MLH)** | Voice AI | ConvAI + Twilio | Phone voice agent with mid-call tool execution |
| **MongoDB (MLH)** | Atlas | Motor async driver | Review queue, context snapshots, transcripts |
| **Zed** | Editor | — | Entire project built in Zed |

---

## Troubleshooting

**API won't start**
- Check `MONGODB_URI` is set and Atlas Network Access allows your IP
- `LAVA_API_KEY` is required even for local dev

**CORS errors in browser**
- Add your exact frontend origin to `CORS_ORIGINS` on the API (must be a JSON array string)
- `localhost` and `127.0.0.1` are different origins — include both
- Redeploy the API after changing `CORS_ORIGINS`

**Voice call connects but agent has no context**
- Verify `ELEVENLABS_AGENT_ID` matches the agent in your ElevenLabs account
- Check Railway logs for `voice.elevenlabs_register_ok` vs `voice.elevenlabs_register_call_failed`
- In the agent system prompt, reference `{{pilotpm_context}}` as a dynamic variable
- Set **Advanced → Audio format** to **μ-law 8000 Hz** in ElevenLabs (required for Twilio)

**Voice tool calls (email / calendar) not firing**
- Confirm both Server Tools are configured in ElevenLabs with the correct Railway URLs
- Check `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` are set for email delivery
- For calendar: set `GOOGLE_SERVICE_ACCOUNT_JSON` (Google Calendar API) or configure SMTP (ICS email fallback)

**Slack `missing_scope` errors**
- Add OAuth scopes (`channels:read`, `channels:history`, `chat:write`, `users:read`) in Slack app settings, reinstall the app, and update `SLACK_BOT_TOKEN`

**No engineers in standup digest**
- Confirm `GITHUB_REPO` is `owner/repo` and the token has read access
- Verify there are commits in the last 24 hours on that repo
- Confirm the Slack bot has been invited to `SLACK_ENGINEERING_CHANNEL`

---

## Scripts

```bash
# Seed MongoDB with synthetic demo data (3 engineers, blockers, sprint)
uv run python scripts/seed_demo_data.py

# Smoke-test all API workflows (requires running server + valid JWT)
uv run python scripts/test_workflows.py
```

---

## Contributing

1. Branch from `main`, make changes, run `uv run ruff check .`
2. Never commit `.env`, `frontend/.env.local`, or any secrets
3. Open a PR against `main`

---

## License

Built for **Y-Hack 2026**. All rights reserved by the team.

---

<div align="center">

Built in 24 hours · **[iloveyhacks.biz](https://www.iloveyhacks.biz)**

</div>
