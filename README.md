# PilotPM

AI project-management orchestrator for YHack 2026: standup digests, blocker radar, sprint drafting (K2 Think V2), status reports, voice agent (Twilio + ElevenLabs), and a human-in-the-loop **review queue** before side effects hit Slack, Monday.com, or email.

## Stack

| Layer | Technology |
|--------|------------|
| API | Python 3.11+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Motor](https://motor.readthedocs.io/) (MongoDB) |
| Frontend | [Next.js](https://nextjs.org/) 16, React 19, Tailwind, Framer Motion, [pnpm](https://pnpm.io/) |
| Data | MongoDB Atlas |
| LLM | Lava forward proxy, optional Gemini, **K2 Think V2** (MBZUAI-IFM) for sprint scoring |

## Repository layout

```
├── app/                 # FastAPI application
│   ├── api/v1/          # HTTP routers (auth, standup, blockers, sprint, reports, voice, review, …)
│   ├── integrations/    # GitHub, Slack, Monday, Hex, Twilio helpers
│   ├── services/        # Business logic
│   ├── repositories/    # Mongo persistence
│   ├── jobs/            # APScheduler background jobs
│   └── main.py          # App factory, CORS, lifespan
├── frontend/            # Next.js dashboard + marketing pages
├── docs/                # PRD, architecture, implementation notes
├── scripts/             # Seed data, workflow smoke tests
├── pyproject.toml       # uv / dependencies
└── uv.lock
```

## Prerequisites

- **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)** (`curl -LsSf https://astral.sh/uv/install.sh | sh` on Unix, or see uv docs for Windows)
- **Node.js 20+** and **pnpm** (`corepack enable && corepack prepare pnpm@latest --activate`)
- **MongoDB** (Atlas URI or local)
- API keys for integrations you plan to use (see [Configuration](#configuration))

## Configuration

Secrets and environment-specific values live in a **`.env` file at the repository root** (not committed; see `.gitignore`). Start from **`.env.example`**:

```bash
cp .env.example .env   # or copy manually on Windows
```

Then edit `.env` with real credentials. The tables below describe each variable.

### Required (minimal backend boot)

| Variable | Purpose |
|----------|---------|
| `DEMO_EMAIL` | Demo login email |
| `DEMO_PASSWORD` | Demo login password |
| `JWT_SECRET` | Strong secret for signing JWTs (e.g. `openssl rand -hex 32`) |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | Database name (default `pilotpm`) |
| `LAVA_API_KEY` | Lava gateway key (or `LAVA_SECRET_KEY`) |
| `K2_API_KEY` | K2 Think API key |
| `GITHUB_TOKEN` | GitHub fine-grained or classic PAT |
| `SLACK_BOT_TOKEN` | Bot token (`xoxb-…`) |
| `MONDAY_API_KEY` | Monday.com API token |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_AGENT_ID` | Voice agent |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE` | Inbound voice webhook |
| `HEX_API_KEY` | Hex analytics embed (reports) |

### Optional / defaults

| Variable | Purpose |
|----------|---------|
| `SLACK_ENGINEERING_CHANNEL` | Channel ID (`C…`) or `#name` for context + blocker Slack reads (default `#engineering`) |
| `SLACK_STANDUP_CHANNEL` | Target for standup digest staging (default `#standup-digest`) |
| `GEMINI_API_KEY` | Fallback LLM |
| `STAKEHOLDER_EMAILS` | Comma-separated BCC targets for reports |
| `SMTP_*` | Optional SMTP for sending mail |
| `CORS_ORIGINS` | JSON array of allowed browser origins, e.g. `["http://localhost:3000","http://127.0.0.1:3000"]` |

**CORS:** `localhost` and `127.0.0.1` are different origins. Include both if you switch URLs. For LAN testing (e.g. `http://192.168.x.x:3000`), add that exact origin.

### Frontend (`frontend/.env.local`)

Copy `frontend/.env.local.example` → `frontend/.env.local`:

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend base URL (no trailing slash), e.g. `http://127.0.0.1:8000` or `http://127.0.0.1:8001` |
| `NEXT_PUBLIC_TWILIO_PHONE` | Optional; shown on Voice page |

**Port conflict:** If another app already uses `8000`, run PilotPM on `8001` and set `NEXT_PUBLIC_API_URL` to match—the login page will error with a clear message if the API is unreachable.

## Run locally

### 1. Backend (repository root)

```bash
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use `--port 8001` if `8000` is taken. Wait until logs show `Application startup complete` and Mongo connected.

- Interactive docs: `http://127.0.0.1:8000/docs` (when `ENV` is not production)
- Health: `GET /health` → status + Mongo check

### 2. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000` (or the URL Next prints). **Sign in** uses the demo account from **`DEMO_EMAIL` / `DEMO_PASSWORD`** in root `.env` (no public sign-up).

JWT is stored in `localStorage` (`pilotpm_token`); API calls send `Authorization: Bearer …`.

## API overview (v1)

All JSON API routes except `/auth/*` expect a valid JWT (see `app/dependencies.py`).

| Area | Examples |
|------|-----------|
| Auth | `POST /auth/login` |
| Standup | `GET/POST .../standup/today`, `POST .../standup/generate` |
| Blockers | `GET/POST .../blockers`, `POST .../blockers/scan`, `PATCH .../blockers/{id}/dismiss` |
| Sprint | `GET .../sprint/current`, `GET .../sprint/draft`, `POST .../sprint/draft/generate`, `PATCH .../sprint/draft/tickets`, `POST .../sprint/approve` |
| Reports | `GET .../reports/current`, `POST .../reports/generate`, `PATCH .../reports/{id}/edit`, `POST .../reports/{id}/send` |
| Voice | `GET .../voice/context`, `GET .../voice/transcripts`; Twilio hits `POST .../voice/webhook/inbound` |
| Review | `GET .../review`, `POST .../review/{id}/approve`, `POST .../review/{id}/reject` |

## Slack troubleshooting

- **`missing_scope`:** Add OAuth scopes (e.g. `channels:read`, `history` as needed), reinstall the app, refresh the bot token.
- **`slack_channel_not_found`:** Set `SLACK_ENGINEERING_CHANNEL` to a real channel ID or name; invite the bot to the channel.

## Scripts

- `scripts/seed_demo_data.py` — populate demo Mongo collections for offline demos
- `scripts/test_workflows.py` — smoke API calls (requires running server + token)

## License / team

Built for **Y-Hack 2026**. Adjust license and attribution in this repo as your team prefers.

## Contributing

1. Create a branch, make changes, run `uv run ruff check .` / tests as you add them.
2. Do not commit `.env`, `frontend/.env.local`, or secrets.
3. Open a PR against `main`.
