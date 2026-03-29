# PilotPM

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4ea94b.svg?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-20232a.svg?style=flat&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Framer Motion](https://img.shields.io/badge/Framer_Motion-black?style=flat&logo=framer&logoColor=blue)](https://www.framer.com/motion/)
[![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=flat&logo=twilio&logoColor=white)](https://www.twilio.com/)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-000000)](https://elevenlabs.io/)
[![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)](https://slack.com/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/)
[![Monday.com](https://img.shields.io/badge/Monday.com-FF3D57?style=flat&logo=monday.com&logoColor=white)](https://monday.com/)

> **No standups. No missed blockers. No manual reports.**

AI project-management orchestrator built in 24 hours at **YHack 2026**. PilotPM watches your GitHub, Slack, and Monday.com 24/7 — generating standup digests, detecting blockers before anyone reports them, planning sprints with K2 Think V2, writing stakeholder reports, and answering questions on a real phone call.

---

## 🚀 Live Demo

| | |
|---|---|
| **Landing Page** | https://www.iloveyhacks.biz |
| **Dashboard** | https://www.iloveyhacks.biz/app/dashboard |
| **Login** | `pm@pilotpm.demo` / `pilotpm2026` |
| **Voice Agent** | Call **(260) 370-3069** — ask anything about the team |
| **API Health** | `GET https://<api-host>/health` |

> **Try the voice agent:** Call (260) 370-3069 and ask *"What's blocking my team?"* or *"Give me the sprint summary."* The AI answers using live GitHub, Slack, and Monday.com data.

---

## What It Does

| Feature | How it works |
|---|---|
| **Async Standup Digest** | Reads GitHub commits, Slack messages, and Monday.com tickets → generates a per-engineer status summary with source citations. Zero meetings. |
| **Blocker Radar** | Detects stale PRs (48h+ no review), blocking Slack language, and engineer inactivity → surfaces cards with pre-drafted resolution pings. |
| **Sprint Autopilot** | Pulls Monday.com backlog → scores every ticket by impact × effort using **K2 Think V2** (MBZUAI) → assigns by velocity and capacity. |
| **Status Reports** | Compiles shipped work, resolved blockers, sprint metrics → writes stakeholder email → stages for one-click Gmail send. |
| **Voice Agent** | Twilio inbound call → ElevenLabs Conversational AI → answers live questions using the same project context snapshot. |
| **Review Queue** | Every agent action (Slack ping, Monday update, email send) lands here first. PM approves, edits, or rejects before anything executes. |

---

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.11, FastAPI, Uvicorn, Motor (async MongoDB) |
| Agents | LangGraph orchestration, APScheduler background jobs |
| AI — General | Gemini 2.0 Flash via **Lava** gateway (primary), Claude fallback |
| AI — Sprint | **K2 Think V2** by MBZUAI (direct API, no rate limit) |
| Voice | ElevenLabs Conversational AI + Twilio |
| Frontend | Next.js 15, React 19, Tailwind CSS, Framer Motion, Three.js |
| Data | MongoDB Atlas |
| Integrations | GitHub API, Slack Web API, Monday.com API |
| Analytics | Hex API (sprint dashboards) |
| Deploy | Railway (API) + Vercel (frontend) |

---

## Repository Layout

```
├── app/
│   ├── api/v1/          # Routers: auth, standup, blockers, sprint, reports, voice, review
│   ├── integrations/    # GitHub, Slack, Monday, Hex, Twilio, ElevenLabs, Gmail
│   ├── services/        # Business logic + LangGraph orchestrator
│   ├── repositories/    # MongoDB queries
│   ├── jobs/            # APScheduler: standup 9am, blocker poll every 15min, Friday report
│   ├── lib/             # LLM router (Lava/K2/Claude), prompts, retry, guardrails
│   ├── models/          # Pydantic schemas
│   └── main.py          # App factory, CORS, lifespan
├── frontend/            # Next.js dashboard + landing page
├── scripts/             # seed_demo_data.py, test_workflows.py
├── docs/                # PRD, architecture, implementation notes
├── pyproject.toml
└── uv.lock
```

---

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**
- **Node.js 20+** and **pnpm** (`corepack enable && corepack prepare pnpm@latest --activate`)
- **MongoDB Atlas** (free M0 tier works)
- API keys for integrations (see Configuration)

---

## Configuration

Copy `.env.example` → `.env` and fill in credentials.

### Required

| Variable | Purpose |
|---|---|
| `DEMO_EMAIL` | Demo login email (`pm@pilotpm.demo`) |
| `DEMO_PASSWORD` | Demo login password |
| `JWT_SECRET` | Random 32-byte hex (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `JWT_EXPIRE_MINUTES` | Set to `1440` for demo day |
| `MONGODB_URI` | Atlas connection string |
| `MONGODB_DB` | Database name (default `pilotpm`) |
| `LAVA_API_KEY` | Lava gateway key |
| `LAVA_BASE` | `https://api.lava.so` |
| `K2_API_KEY` | K2 Think V2 key (MBZUAI) |
| `K2_API_BASE` | `https://api.k2think.ai` |
| `GITHUB_TOKEN` | Fine-grained PAT with repo read |
| `GITHUB_REPO` | `owner/repo` (e.g. `acme/acme-api`) |
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-…`) |
| `MONDAY_API_KEY` | Monday.com API token |
| `MONDAY_BOARD_ID` | Sprint board ID (from URL) |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_AGENT_ID` | ConvAI agent ID |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_PHONE` | E.164 number (e.g. `+12603703069`) |

### Optional

| Variable | Purpose |
|---|---|
| `SLACK_ENGINEERING_CHANNEL` | Channel ID (`C…`) for blocker reads (default `#engineering`) |
| `SLACK_STANDUP_CHANNEL` | Channel ID for standup posts |
| `HEX_API_KEY` | Hex analytics embed (reports page) |
| `GEMINI_API_KEY` | Last-resort fallback if Lava fails |
| `STAKEHOLDER_EMAILS` | Comma-separated report recipients |
| `CORS_ORIGINS` | JSON array of allowed browser origins |

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000   # or Railway URL in production
NEXT_PUBLIC_TWILIO_PHONE=+12603703069
```

---

## Run Locally

### 1. Backend

```bash
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Docs: `http://127.0.0.1:8000/docs`
- Health: `GET http://127.0.0.1:8000/health`

### 2. Seed Demo Data

```bash
uv run python scripts/seed_demo_data.py
```

Populates MongoDB with 3 synthetic engineers, realistic commits, blockers, and sprint tickets.

### 3. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000` → sign in with `pm@pilotpm.demo` / `pilotpm2026`.

---

## Deploy

### API → Railway

- Start command in `railpack.json`: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Copy all `.env` variables into Railway service settings
- MongoDB Atlas → Network Access → allow `0.0.0.0/0` for demo

### Frontend → Vercel

1. Import repo → set **Root Directory** to `frontend`
2. Add env vars:
   - `NEXT_PUBLIC_API_URL` = `https://<your-service>.up.railway.app`
   - `NEXT_PUBLIC_TWILIO_PHONE` = `+12603703069`
3. Update `CORS_ORIGINS` on Railway:
```json
["https://www.iloveyhacks.biz","http://localhost:3000","http://127.0.0.1:3000"]
```

### Twilio Voice Webhook

In Twilio Console → Phone Numbers → **(260) 370-3069** → Voice webhook:
```
POST https://<api-host>/api/v1/voice/webhook/inbound
```

> Set ElevenLabs agent Audio → μ-law 8000 Hz for Twilio compatibility.

---

## Agentic Workflows

### Mental Model

```
GitHub + Slack + Monday.com
        ↓
  context_builder (cached 15min)
        ↓
  LangGraph Orchestrator
   ├── StandupAgent   → digest + citations
   ├── BlockerAgent   → cards + draft pings
   ├── SprintAgent    → K2 scores + capacity
   ├── ReportAgent    → stakeholder email
   └── VoiceAgent     → telephony context
        ↓
  Review Queue (human approval gate)
        ↓
  Execute: Slack / Monday.com / Gmail / Calendar
```

### Context Layer

`context_builder.build_context_snapshot()` fetches GitHub + Slack + Monday in parallel and caches in MongoDB (`≤15min` TTL). All agents and voice use the same snapshot — no redundant API calls.

### Review Queue (Human-in-the-Loop)

Every action that touches the outside world is staged as a `pending` document in `review_queue`. The PM approves, edits, or rejects from the dashboard before anything executes.

### Scheduled Jobs

| Job | Schedule | Purpose |
|---|---|---|
| `context_refresh` | Every 15 min | Keep project snapshot fresh |
| `daily_standup` | 09:00 ET daily | Generate digest + stage Slack post |
| `blocker_poll` | Every 15 min, 08:00–20:00 ET | Scan for new blockers |
| `weekly_report` | Friday 17:00 ET | Generate + stage stakeholder report |

### AI Routing

```
task = "sprint" or "backlog"  →  K2 Think V2 (MBZUAI)
                                    ↓ fail
                                 Lava/Gemini fallback

everything else               →  Gemini 2.0 Flash via Lava
                                    ↓ fail
                                 Claude via Lava fallback
```

---

## API Reference

All routes except `/auth/*` require `Authorization: Bearer <jwt>`.

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login` |
| Standup | `GET /standup/today` · `POST /standup/generate` · `GET /standup/history` |
| Blockers | `GET /blockers` · `POST /blockers/scan` · `PATCH /blockers/{id}/dismiss` |
| Sprint | `GET /sprint/draft` · `POST /sprint/draft/generate` · `PATCH /sprint/draft/tickets` · `POST /sprint/approve` |
| Reports | `GET /reports/current` · `POST /reports/generate` · `POST /reports/{id}/send` |
| Voice | `GET /voice/context` · `GET /voice/transcripts` · `POST /voice/webhook/inbound` (Twilio, no JWT) |
| Review | `GET /review` · `POST /review/{id}/approve` · `POST /review/{id}/reject` · `POST /review/approve-batch` |

---

## Team

Built in 24 hours at **Y-Hack 2026** by Team PilotPM.
