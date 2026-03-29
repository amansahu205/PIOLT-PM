# PilotPM

AI project-management orchestrator for YHack 2026: standup digests, blocker radar, sprint drafting (K2 Think V2), status reports, voice agent (Twilio + ElevenLabs), and a human-in-the-loop **review queue** before side effects hit Slack, Monday.com, or email.

How those pieces run end-to-end is documented in **[Agentic workflows](#agentic-workflows)** below.

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

## Deploy API (Railway)

- **Start command:** `railpack.json` runs `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Override in the Railway UI if needed.
- **Env:** Copy variables from `.env.example` into the Railway service (`MONGODB_URI`, `JWT_SECRET`, `DEMO_*`, integrations, etc.).
- **MongoDB Atlas → Network Access:** Allow traffic from your deploy host. For Railway (changing egress IPs), add **`0.0.0.0/0`** for demos or use [Railway static egress](https://docs.railway.com/reference/static-outbound-ip). If the cluster blocks your IP, Atlas may surface errors like `TLSV1_ALERT_INTERNAL_ERROR` during TLS.
- The API passes **`tlsCAFile=certifi.where()`** to Motor so Atlas verifies against a full CA bundle in minimal containers.

## Vercel and Twilio (production setup)

Do this **after** the API is live on a public HTTPS URL (e.g. Railway). Order: **Vercel + CORS** (browser → API), then **Twilio** (PSTN → API).

### Vercel (frontend)

1. **[Vercel Dashboard](https://vercel.com/dashboard)** → **Add New…** → **Project** → import your GitHub repo.
2. **Root Directory:** `frontend` (this repo is a monorepo).
3. **Framework Preset:** Next.js. Install command should be `pnpm install`; build `pnpm build` (Vercel usually detects this when it sees `pnpm-lock.yaml`).
4. **Environment Variables** — add for **Production** (and **Preview** if you test PRs):

   | Name | Value |
   |------|--------|
   | `NEXT_PUBLIC_API_URL` | Your API origin only: `https://<your-service>.up.railway.app` — **no path, no trailing slash** |
   | `NEXT_PUBLIC_TWILIO_PHONE` | Optional — E.164, e.g. `+1…`, shown on the Voice dashboard page |

5. **Deploy.** Note the site URL (e.g. `https://piolt-pm.vercel.app`).
6. **Fix CORS on Railway:** In the API service variables, set `CORS_ORIGINS` to valid JSON listing **exact** origins the browser will use, for example:

   ```json
   ["https://piolt-pm.vercel.app","http://localhost:3000","http://127.0.0.1:3000"]
   ```

   Replace `piolt-pm.vercel.app` if your Vercel hostname differs. Add each **preview** URL separately if you need them (patterns like `*.vercel.app` are not valid in standard CORS). Redeploy the **API** after changing `CORS_ORIGINS`.
7. **Smoke test:** Open `https://<api>/health` in a browser, then sign in on the Vercel URL using **`DEMO_EMAIL` / `DEMO_PASSWORD`** from the API’s env. If login fails with CORS in the console, the Vercel origin is missing from `CORS_ORIGINS`.

### Twilio (inbound voice)

Twilio sends **HTTP POST** to your **API**, not to Vercel. Localhost will not work.

1. **Railway (API) env** — ensure these are set (same names as `.env.example`):

   | Variable | Purpose |
   |----------|---------|
   | `TWILIO_ACCOUNT_SID` | From [Twilio Console](https://console.twilio.com/) → Account |
   | `TWILIO_AUTH_TOKEN` | Account auth token |
   | `TWILIO_PHONE` | Your Twilio number in **E.164** (e.g. `+15551234567`) |
   | `ELEVENLABS_API_KEY` | [ElevenLabs](https://elevenlabs.io/) API key (`xi-api-key` for register-call) |
   | `ELEVENLABS_AGENT_ID` | Conversational AI agent ID that supports **telephony / Twilio** |

   Redeploy after changing secrets.

2. **Twilio Console** → **Phone Numbers** → **Manage** → **Active numbers** → select your number.
3. Under **Voice & Fax** → **A CALL COMES IN**: choose **Webhook**, **HTTP POST**.
4. **URL:** `https://<your-api-host>/api/v1/voice/webhook/inbound`  
   Example: `https://piolt-pm-production.up.railway.app/api/v1/voice/webhook/inbound`
5. Save. (PilotPM does not validate Twilio request signatures on this route yet; no extra “auth” setting is required in Twilio for the webhook itself.)

**Twilio trial accounts:** Inbound callers may hear a trial disclaimer and be asked to **press a key**. Twilio can then **POST the voice webhook again** for the same `CallSid`. PilotPM **reuses cached TwiML** for that call and **upserts** transcript rows so ElevenLabs `register-call` is not invoked twice (which would drop the call). Add billing / upgrade Twilio to remove the trial prompt entirely for demos.

**Call flow:** Twilio POSTs form data → PilotPM loads Mongo-backed context → **`POST https://api.elevenlabs.io/v1/convai/twilio/register-call`** (see [Register Twilio calls](https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/register-call)) with `agent_id`, `From` / `To`, and **`conversation_initiation_client_data.dynamic_variables`** (`caller_number`, **`pilotpm_context`** = the live PM summary text). ElevenLabs returns **TwiML** you return to Twilio. On failure, the caller hears a **Polly** error message.

**Agent instructions:** In the ConvAI agent’s system prompt (or first message), reference **`{{pilotpm_context}}`** so the model uses the injected snapshot. If you omit it, calls still connect when dynamic variables work, but the agent won’t read PilotPM’s live context unless a fallback **`conversation_config_override`** attempt succeeds (see server logs).

**ElevenLabs:** Prefer the **register-call** flow above for custom Twilio webhooks; the [native Twilio integration](https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/native-integration) is simpler if you hand phone numbers to ElevenLabs instead.

**If the call never reaches the agent (silence / hang-up / generic error):** Set **Voice → TTS** and **Advanced → input format** to **μ-law 8000 Hz** (required for Twilio). Confirm **`ELEVENLABS_AGENT_ID`** is the ConvAI agent ID. Check Railway logs for **`voice.elevenlabs_register_call_failed`**, **`voice.elevenlabs_register_ok`**, or **`voice.inbound_failed`** after a test call.

### Quick checklist

| Step | Done when |
|------|-----------|
| API | `GET https://<api>/health` returns OK |
| Vercel | Site loads, login works |
| CORS | Browser devtools: no CORS errors on `POST /auth/login` |
| Voice | Outbound test call to `TWILIO_PHONE` connects to the agent |

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

## Agentic workflows

Most automations read a **cached project snapshot** (GitHub + Slack + Monday) instead of hammering APIs on every request. Voice uses the same world model, condensed for telephony.

### Shared context layer

- **`context_builder.build_context_snapshot()`** fetches the three integrations in parallel and stores **`project_context`** in MongoDB (`sources_available` marks what succeeded).
- **`get_context_snapshot()`** returns that document if it is **≤ 15 minutes** old; otherwise it refreshes.
- On API startup, the app **warms** context once; the scheduler also refreshes it **every 15 minutes** (`app/jobs/context_job.py`).

### Human-in-the-loop: review queue

Workflows that would change the outside world (Slack post, Monday update, email send) call **`review_service.stage_action(...)`**, which inserts a **`pending`** document into Mongo **`review_queue`** (`type`, `data`, `reasoning`, `workflow`).

The dashboard **Review** page and **`GET /api/v1/review`** list pending items; **`POST .../approve`** and **`POST .../reject`** update their status. Treat this as the **approval gate** before side effects; wire execution workers separately if you need approve-to-execute automation.

### Standup digest (`workflow: standup`)

| Step | What happens |
|------|----------------|
| Input | Cached context (GitHub / Slack / Monday) + optional GitHub team member names. |
| Agent | LLM with `Prompts.STANDUP_*` produces structured JSON (per-engineer status, blockers, etc.). |
| Persist | Validated digest → standup repository + `standup_cache` on context. |
| Stage | **`slack_message`** to **`SLACK_STANDUP_CHANNEL`** with formatted digest text. |

**Triggers:** **`POST /api/v1/standup/generate`** (manual / UI) and cron **09:00 America/New_York** daily (`app/jobs/standup_job.py`). **Read:** `GET /api/v1/standup/today`.

### Blocker radar (`workflow: blocker`)

| Step | What happens |
|------|----------------|
| Input | Open PRs + ages, recent Slack messages, stale Monday “in progress” items, per-engineer commits (sanitized). |
| Agent | LLM with `Prompts.BLOCKER_*` returns JSON blocker candidates. |
| Persist | New **`BlockerCard`** rows (deduped). |
| Stage | For each new blocker, **`slack_ping`** to **`SLACK_ENGINEERING_CHANNEL`** with `draft_ping` (or fallback text). |

**Triggers:** **`POST /api/v1/blockers/scan`** and cron **every 15 minutes** between **08:00–20:00 ET** (`app/jobs/blocker_job.py`). **Dismiss:** `PATCH /api/v1/blockers/{id}/dismiss`.

### Sprint autopilot (`workflow: sprint`)

| Step | What happens |
|------|----------------|
| Draft | **`POST /api/v1/sprint/draft/generate`** — Monday/GitHub-style inputs → LLM with **`task=sprint`** and **K2 Think** (`Prompts.SPRINT_*`) → scored tickets, capacity, utilization. |
| Edit | **`PATCH /api/v1/sprint/draft/tickets`** toggles inclusion and recomputes utilization (max **110%** allowed on approve). |
| Approve | **`POST /api/v1/sprint/approve`** stages **`monday_sprint`** (apply plan to board) and **`calendar_events`** (ceremony placeholders). |

**Read:** `GET /api/v1/sprint/current` (board snapshot), `GET /api/v1/sprint/draft`.

### Weekly status report (`workflow: reports`)

| Step | What happens |
|------|----------------|
| Generate | Context snapshot + merged PRs (7d), resolved/active blockers, Monday tickets → LLM **`Prompts.REPORT_*`** → subject/body; optional **Hex** embed URL. |
| Send | **`POST /api/v1/reports/{id}/send`** stages **`gmail_send`** (`STAKEHOLDER_EMAILS`, subject, body) and marks the report **sent**. |

**Triggers:** **`POST /api/v1/reports/generate`**, cron **Friday 17:00 America/New_York** (`app/jobs/report_job.py`).

### Voice agent (F-005)

| Step | What happens |
|------|----------------|
| Inbound | Twilio **`POST /api/v1/voice/webhook/inbound`** (no JWT). |
| Context | **`VoiceService`** builds a **system prompt** from **`get_context_for_voice()`** (sprint, blockers, standup digest, recent GitHub activity summary). |
| Bridge | TwiML connects the call to **ElevenLabs** WebSocket; **`pilotpm_context`** is passed as a **dynamic variable** (and prompt-override fallback) for the agent. |
| Log | Calls recorded in **`call_transcripts`** (dashboard: `GET /api/v1/voice/transcripts`). |

### Scheduled jobs (APScheduler, `America/New_York`)

| Job ID | Schedule | Purpose |
|--------|----------|---------|
| `context_refresh` | Every **15 minutes** | Refresh `project_context` |
| `daily_standup` | Daily **09:00** | Generate standup + stage Slack post |
| `blocker_poll` | ***/15** in **08–20** | Run blocker scan + stage pings |
| `weekly_report` | **Friday 17:00** | Generate weekly report draft |

Defined in **`app/jobs/scheduler.py`**.

### Mental model

**Integrations → context cache → LLM planners (standup / blockers / sprint / report) → Mongo + review queue for external actions → Voice** answers live using the same snapshot narrative.

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
