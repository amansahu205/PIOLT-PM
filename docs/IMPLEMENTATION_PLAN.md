# IMPLEMENTATION_PLAN.md — Build Order & Execution Roadmap

> **Version**: 1.0 | **Last Updated**: March 28, 2026
> **Project**: PilotPM — YHack 2026
> **Deadline**: 11:00am Sunday March 29, 2026 (24 hours)
> **Team**: 3–4 people
> **References**: PRD.md, APP_FLOW.md, AI_ARCHITECTURE.md, BACKEND_STRUCTURE.md

---

## 0. How to Use This With AI Agents

When using Cursor / Claude Code / Copilot / Windsurf, prefix every prompt with:

```
/mem init — PilotPM, FastAPI+LangGraph+MongoDB, 24hr hackathon, GSD mode
You are building PilotPM — an AI PM orchestrator for software teams.
Read IMPLEMENTATION_PLAN.md Phase [X] Step [Y] and implement exactly what it says.
Reference: [doc name] Section [N].
Do not add features not listed. Do not change the file structure.
Stack: Python 3.11, FastAPI, Motor (async MongoDB), APScheduler, LangGraph.
No SQLModel. No Alembic. No PostgreSQL. No pip — use uv only.
```

Every step has:
- Exact bash commands to run
- Exact files to create with their source doc reference
- A checklist to verify before moving to the next step
- The AI prompt to use if you're delegating that step

---

## 1. Build Principles

- **Vertical slices**: DB → service → API → test per feature. Never build all models first.
- **Docs before code**: Reference the doc section before writing a single line.
- **No scope creep**: If a feature isn't in PRD.md, it doesn't get built.
- **uv only**: Never use pip. Every `pip install` = wrong.
- **Test as you go**: Every step has a curl or Python check. Don't skip them.
- **Demo data first**: Seed MongoDB with 3 fake engineers before building any UI.
- **Commit every working step**: `git commit -m "feat: F-001 standup agent working"`

---

## 2. Team Split (4 people)

| Person | Owns | Hours |
|--------|------|-------|
| **P1** | Foundation + F-001 (standup) + F-002 (blockers) | 0–14h |
| **P2** | F-003 (sprint) + F-010 (backlog) + K2 integration | 0–14h |
| **P3** | F-004 (reports) + F-005 (voice) + Twilio/ElevenLabs | 2–16h |
| **P4** | Frontend (Lovable/v0) + Devpost + demo prep | 6–24h |

All 4 merge at hour 14 for integration, hour 20 for polish, hour 22 for demo rehearsal.

---

## 3. 24-Hour Timeline

```
11:00am Sat  ┌─ PHASE 1: Foundation (P1 leads, all help)
             │  uv init, .env, MongoDB, LLM client, context builder
01:00pm Sat  ├─ PHASE 2: Data Pipeline
             │  GitHub + Slack + Monday.com integrations
             │  Seed demo data
03:00pm Sat  ├─ PHASE 3: P0 Features (P1+P2+P3 parallel)
             │  F-001 Standup ────────────────────── P1
             │  F-002 Blockers ───────────────────── P1
             │  F-003 Sprint (K2) ────────────────── P2
             │  F-004 Reports (Hex) ──────────────── P3
07:00pm Sat  ├─ PHASE 4: Voice Agent (P3)
             │  Twilio + ElevenLabs Conversational AI
             │  Real phone call working
10:00pm Sat  ├─ PHASE 5: Review Queue (P1)
             │  All actions staged, approve/reject/edit working
11:00pm Sat  ├─ PHASE 6: Frontend (P4 leads)
             │  Lovable/v0 scaffolding, wire to backend
03:00am Sun  ├─ PHASE 7: Integration + Polish
             │  All workflows end-to-end
             │  Demo data seeded
             │  Fallbacks tested
07:00am Sun  ├─ PHASE 8: Devpost + Assets
             │  Veo video, Stitch images, landing page
09:00am Sun  ├─ PHASE 9: Pre-Demo Checklist
             │  3 full demo rehearsals
10:00am Sun  └─ PHASE 10: Submit
               Devpost submitted by 10:30am (30min buffer)
11:00am Sun  DEADLINE
```

---

## Phase 1: Foundation (11:00am – 1:00pm, ~2 hours)

### Step 1.1 — Initialize Project

**AI Agent Prompt:**
```
Initialize a Python 3.11 FastAPI project using uv.
Project name: pilotpm
Create the full folder structure from BACKEND_STRUCTURE.md Section 2.
Do not create any feature files yet — only the skeleton.
```

```bash
# Run these commands exactly
curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir pilotpm && cd pilotpm
uv init
uv python pin 3.11

# Core dependencies
uv add fastapi "uvicorn[standard]" pydantic pydantic-settings
uv add motor pymongo                        # async MongoDB
uv add "python-jose[cryptography]" passlib  # JWT auth
uv add httpx                               # Lava gateway + K2 + integrations
uv add langgraph langchain                 # agent orchestration
uv add apscheduler                         # background jobs (standup 9am etc)
uv add slowapi                             # rate limiting
uv add structlog                           # JSON logging
uv add twilio                              # voice webhook
uv add python-multipart python-dotenv

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx ruff

# Create folder structure (BACKEND_STRUCTURE.md §2)
mkdir -p app/{api/v1,services,repositories,integrations,lib,models,db,jobs}
touch app/__init__.py app/main.py app/config.py app/dependencies.py
touch app/db/__init__.py app/db/mongo.py app/db/indexes.py
touch app/lib/__init__.py app/lib/llm.py app/lib/prompts.py
touch app/lib/retry.py app/lib/cost.py app/lib/guardrails.py
touch app/lib/logging_config.py
touch app/models/__init__.py app/models/common.py app/models/auth.py
touch app/models/standup.py app/models/blocker.py app/models/sprint.py
touch app/models/report.py app/models/review.py app/models/voice.py
touch app/api/__init__.py app/api/v1/__init__.py
touch app/api/v1/{auth,standup,blockers,sprint,reports,voice,backlog,review,health}.py
touch app/services/__init__.py
touch app/repositories/__init__.py app/repositories/base.py
touch app/integrations/__init__.py
touch app/jobs/__init__.py app/jobs/scheduler.py
touch app/jobs/{standup_job,blocker_job,context_job,report_job}.py
touch app/services/{auth_service,context_builder,orchestrator}.py
touch app/services/{standup_service,blocker_service,sprint_service}.py
touch app/services/{report_service,voice_service,backlog_service,review_service}.py
touch app/repositories/{standup_repo,blocker_repo,sprint_repo}.py
touch app/repositories/{report_repo,review_repo,context_repo,transcript_repo}.py
touch app/integrations/{github_service,slack_service,monday_service}.py
touch app/integrations/{gmail_service,calendar_service,hex_service}.py
touch app/integrations/{elevenlabs_service,twilio_service}.py

git init
echo -e "__pycache__/\n*.pyc\n.env\n.venv/\n.ruff_cache/" > .gitignore
git add . && git commit -m "chore: project skeleton"
```

**Checklist:**
- [ ] `uv run python -c "import fastapi; print('ok')"` passes
- [ ] All folders exist per BACKEND_STRUCTURE.md §2
- [ ] `.gitignore` includes `.env`

---

### Step 1.2 — Environment Config

**AI Agent Prompt:**
```
Create app/config.py for PilotPM using pydantic-settings.
Reference: BACKEND_STRUCTURE.md Section 4 (Config).
Include all env vars: DEMO_EMAIL, DEMO_PASSWORD, JWT_SECRET,
MONGODB_URI, MONGODB_DB, LAVA_API_KEY, LAVA_BASE, K2_API_KEY,
K2_API_BASE, GITHUB_TOKEN, SLACK_BOT_TOKEN, MONDAY_API_KEY,
ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, TWILIO_ACCOUNT_SID,
TWILIO_AUTH_TOKEN, TWILIO_PHONE, HEX_API_KEY, STAKEHOLDER_EMAILS,
CORS_ORIGINS. Use @lru_cache. Add get_settings() function.
```

```bash
# Create .env from example (BACKEND_STRUCTURE.md §18)
cat > .env << 'EOF'
ENV=development
DEMO_EMAIL=pm@pilotpm.demo
DEMO_PASSWORD=pilotpm2026
JWT_SECRET=change-me-use-openssl-rand-hex-32
JWT_EXPIRE_MINUTES=480
MONGODB_URI=mongodb+srv://...
MONGODB_DB=pilotpm
LAVA_API_KEY=your_lava_key_here
LAVA_BASE=https://api.lava.so
# Optional: GEMINI_API_KEY= / GEMINI_MODEL= — last resort if Lava fails
K2_API_KEY=your_k2_key_here
K2_API_BASE=https://api.k2think.ai
GITHUB_TOKEN=ghp_...
SLACK_BOT_TOKEN=xoxb-...
MONDAY_API_KEY=...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE=+1...
HEX_API_KEY=...
STAKEHOLDER_EMAILS=judge@yhack.org
EOF
```

**Checklist:**
- [ ] `uv run python -c "from app.config import settings; print(settings.DEMO_EMAIL)"` prints `pm@pilotpm.demo`
- [ ] App exits with clear error if `MONGODB_URI` is missing

---

### Step 1.3 — MongoDB + Logging Setup

**AI Agent Prompt:**
```
Implement app/db/mongo.py with Motor async client.
Reference: BACKEND_STRUCTURE.md Section 5.
Implement: connect_mongo(), close_mongo(), get_db(), get_collection(name).
Then implement app/db/indexes.py with ensure_indexes(db) creating all indexes listed.
Then implement app/lib/logging_config.py with configure_logging() using structlog JSON renderer.
Reference: BACKEND_STRUCTURE.md Section 16.
```

**Checklist:**
- [ ] `uv run python -c "import asyncio; from app.db.mongo import connect_mongo; asyncio.run(connect_mongo()); print('mongo ok')"` prints `mongo ok`
- [ ] MongoDB Atlas shows `pilotpm` database created

---

### Step 1.4 — LLM Client (Critical — everything depends on this)

**AI Agent Prompt:**
```
Implement app/lib/llm.py for PilotPM.
Reference: AI_ARCHITECTURE.md Section 3.
Implement exactly:
- call_via_lava — POST {LAVA_BASE}/v1/forward?u={LAVA_FORWARD_UPSTREAM}, OpenAI-style body
- call_k2 — MBZUAI K2 direct at K2_API_BASE
- call_via_gemini (optional) — google-genai when GEMINI_API_KEY set
- call_ai — unified router: sprint/backlog → K2 then Lava×2 then optional Gemini; else Lava×2 then optional Gemini
Use settings from app.config (LAVA_*, K2_*, GEMINI_*).
Log all calls via structlog; import log_llm_cost from app.lib.cost.
```

**AI Agent Prompt (retry decorator):**
```
Implement app/lib/retry.py with llm_retry decorator.
Reference: AI_ARCHITECTURE.md Section 10.
Exponential backoff with jitter. max_retries=3, base_delay=1.0, max_delay=10.0.
Async only. Log each retry attempt with structlog.
```

**AI Agent Prompt (prompts):**
```
Implement app/lib/prompts.py with the Prompts class.
Reference: AI_ARCHITECTURE.md Section 4.
Include all 7 prompts exactly as written:
CLASSIFIER_SYSTEM, CLASSIFIER_USER,
STANDUP_SYSTEM, STANDUP_USER,
BLOCKER_SYSTEM, BLOCKER_USER,
SPRINT_SYSTEM, SPRINT_USER,
REPORT_SYSTEM, REPORT_USER,
BACKLOG_SYSTEM, BACKLOG_USER,
VOICE_SYSTEM.
Never write prompts inline in agents — always import from this class.
```

```bash
# Smoke test LLM client
uv run python -c "
import asyncio
from app.lib.llm import call_ai
result = asyncio.run(call_ai('You are helpful.', 'Say: PILOTPM OK', task='general'))
print(result)
"
```

**Checklist:**
- [ ] `call_ai()` returns a string from Lava (or Gemini if Lava failed and GEMINI_API_KEY is set)
- [ ] `call_ai(task='sprint')` routes to K2 (check logs)
- [ ] If both Lava attempts fail and `GEMINI_API_KEY` is set, logs show `llm.using_gemini_direct_fallback`
- [ ] `llm_retry` retries on exception with backoff

---

### Step 1.5 — Auth Service + Main App

**AI Agent Prompt:**
```
Implement app/services/auth_service.py for PilotPM.
Reference: BACKEND_STRUCTURE.md Section 7.
Single hardcoded demo user from .env (DEMO_EMAIL, DEMO_PASSWORD).
No user database. Functions: verify_credentials(email, password) -> bool,
create_jwt(user) -> str, decode_jwt(token) -> dict | None.
Use python-jose HS256. JWT_SECRET and JWT_EXPIRE_MINUTES from settings.
```

**AI Agent Prompt:**
```
Implement app/dependencies.py for PilotPM.
Reference: BACKEND_STRUCTURE.md Section 6.
Implement get_current_user(credentials) using HTTPBearer.
Calls decode_jwt from auth_service. Raises 401 if invalid.
Returns payload dict with email and role.
Also implement get_db_dep() returning get_db() from app.db.mongo.
```

**AI Agent Prompt:**
```
Implement app/main.py for PilotPM.
Reference: BACKEND_STRUCTURE.md Section 3.
Use create_app() factory pattern with lifespan context manager.
Lifespan: connect_mongo(), start_scheduler(), build_context_snapshot().
Add: CORSMiddleware, LoggingMiddleware, RequestIDMiddleware, slowapi rate limiter.
Global exception handlers for Exception and ValueError.
Include all routers from app/api/v1/ with correct prefixes.
Implement app/middleware.py with RequestIDMiddleware and LoggingMiddleware.
Reference: BACKEND_STRUCTURE.md Section 14.
```

```bash
uv run uvicorn app.main:app --reload --port 8000
# In another terminal:
curl http://localhost:8000/health
# Expected: {"status": "ok", "gemini_via_lava": true, "mongo": true}

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pm@pilotpm.demo","password":"pilotpm2026"}'
# Expected: {"access_token": "eyJ...", "token_type": "bearer"}
```

**Checklist:**
- [ ] `GET /health` returns 200 with mongo status
- [ ] `POST /auth/login` with correct creds returns JWT
- [ ] `POST /auth/login` with wrong creds returns 401
- [ ] `GET /docs` shows all routes
- [ ] Server starts without errors in logs

---

## Phase 2: Data Pipeline (1:00pm – 3:00pm, ~2 hours)

### Step 2.1 — Seed Demo Data

**Create this first — all agents need realistic data to work with.**

**AI Agent Prompt:**
```
Create scripts/seed_demo_data.py for PilotPM.
Insert into MongoDB:
1. 3 synthetic engineers: Sarah Ali, Tom Kim, Mike Ross
2. GitHub activity: 12 commits (4 each), 5 open PRs (2 by Tom, 2 by Sarah, 1 by Mike)
   - PR #143 by Sarah, open 52 hours, 0 reviews (triggers blocker)
   - Mike has 0 commits in last 24 hours (triggers inactivity flag)
   - Tom has message "waiting on API keys" in Slack (triggers blocker)
3. Monday.com board snapshot: Sprint 24, 14 tickets, 6 in-progress
4. Slack messages: realistic #engineering channel messages from last 48 hours
   - Include: "still waiting on those keys" from sarah_ali
   - Include: 3 PR review requests from tom_kim
Store in MongoDB collections: demo_github, demo_slack, demo_monday
```

```bash
uv run python scripts/seed_demo_data.py
# Verify in MongoDB Atlas or:
uv run python -c "
import asyncio
from app.db.mongo import connect_mongo, get_collection
async def check():
    await connect_mongo()
    col = get_collection('demo_github')
    count = await col.count_documents({})
    print(f'GitHub docs: {count}')
asyncio.run(check())
"
```

**Checklist:**
- [ ] `demo_github` collection has 12+ commit documents
- [ ] `demo_slack` has 30+ message documents including the blocking language
- [ ] `demo_monday` has sprint + backlog ticket documents
- [ ] PR #143 exists with `reviews: 0` and `age_hours: 52`

---

### Step 2.2 — Integration Services

**AI Agent Prompt (GitHub):**
```
Implement app/integrations/github_service.py for PilotPM.
Class GitHubService with async static methods:
- get_recent_activity(hours=24) -> dict  — commits, PRs, reviews per engineer
- get_open_prs_with_age() -> list  — PRs with hours_open and review_count
- get_commit_activity_per_engineer() -> dict  — engineer -> commit count
- get_velocity_per_engineer(sprints=3) -> dict  — engineer -> avg story points
- get_team_members() -> list[str]  — engineer names from recent commits
Use GITHUB_TOKEN from settings. Base URL: https://api.github.com.
For demo: fall back to demo_github MongoDB collection if API call fails.
Use httpx AsyncClient. Add @llm_retry where appropriate.
```

**AI Agent Prompt (Slack):**
```
Implement app/integrations/slack_service.py for PilotPM.
Class SlackService with async static methods:
- get_recent_messages(hours=48, channel="#engineering") -> list
- post_message(channel, text) -> bool
- send_dm(user_handle, text) -> bool
Use SLACK_BOT_TOKEN from settings. Base URL: https://slack.com/api.
For demo: fall back to demo_slack MongoDB collection if API call fails.
Rate limit: max 1 request/second (add asyncio.sleep(1) between calls).
```

**AI Agent Prompt (Monday.com):**
```
Implement app/integrations/monday_service.py for PilotPM.
Class MondayService with async static methods:
- get_sprint_status() -> dict  — current sprint name, tickets, velocity%
- get_backlog() -> list  — all tickets not in a sprint
- get_incomplete_tickets() -> list  — in-progress tickets
- get_current_sprint_number() -> int
- get_stale_in_progress_tickets() -> list  — tickets in-progress > 3 days
- create_board(name, tasks) -> str  — board ID
- update_task_status(task_id, status) -> bool
Use MONDAY_API_KEY from settings. GraphQL API: https://api.monday.com/v2.
For demo: fall back to demo_monday MongoDB collection if API call fails.
```

**Checklist:**
- [ ] `GitHubService.get_recent_activity()` returns dict with engineer keys
- [ ] `SlackService.get_recent_messages()` returns list with > 0 messages
- [ ] `MondayService.get_backlog()` returns list with > 5 tickets
- [ ] All services fall back to demo data gracefully when real API fails

---

### Step 2.3 — Context Builder

**AI Agent Prompt:**
```
Implement app/services/context_builder.py for PilotPM.
Reference: AI_ARCHITECTURE.md Section 5.
Implement exactly:
- build_context_snapshot() -> dict  — fetch GitHub+Slack+Monday in parallel with asyncio.gather
- get_context_snapshot() -> dict  — return cache if < 15 min old, else rebuild
- get_context_for_voice() -> dict  — condensed context for ElevenLabs system prompt
- _format_blockers_for_voice(ctx) -> str
- _format_standup_for_voice(ctx) -> str
- _format_activity_for_voice(ctx) -> str
Cache in MongoDB collection "project_context". CONTEXT_TTL_MINUTES = 15.
Log sources_available dict after every refresh.
```

```bash
uv run python -c "
import asyncio
from app.db.mongo import connect_mongo
from app.services.context_builder import build_context_snapshot
async def test():
    await connect_mongo()
    ctx = await build_context_snapshot()
    print('Sources:', ctx['sources_available'])
    print('Refreshed at:', ctx['refreshed_at'])
asyncio.run(test())
"
```

**Checklist:**
- [ ] Context snapshot builds in < 10 seconds
- [ ] `sources_available` shows which APIs responded
- [ ] Cached version returned on second call
- [ ] `get_context_for_voice()` returns condensed string suitable for ElevenLabs prompt

---

## Phase 3: P0 Features (3:00pm – 11:00pm, ~8 hours)

> P1 + P2 + P3 work in parallel. Each person takes their assigned features.

---

### Step 3.1 — F-001: Async Standup Digest (P1)

**Reference**: PRD.md F-001, AI_ARCHITECTURE.md Section 7 (standup_agent.py), BACKEND_STRUCTURE.md Section 9

**AI Agent Prompt:**
```
Implement the standup workflow for PilotPM — F-001.

1. app/repositories/standup_repo.py
   - BaseRepository subclass, collection="standup_digests"
   - find_today() -> dict | None  — digest with generated_at > today 6am
   - insert(digest) -> dict
   - find_recent(n=7) -> list

2. app/services/standup_service.py
   - generate_digest(db) -> dict  — full pipeline:
     a. get_context_snapshot() from context_builder
     b. build STANDUP_USER prompt with context data
     c. call call_ai(system=Prompts.STANDUP_SYSTEM, user=..., task="general", temperature=0.3)
     d. parse JSON output with _parse_json_output()
     e. validate with OutputGuardrails.validate_standup_output()
     f. cache in MongoDB (standup_cache in project_context)
     g. stage Slack post action in review queue
     h. return digest
   - get_today_digest(db) -> dict  — return cached or generate
   - get_history(db) -> list

3. app/api/v1/standup.py
   - GET /api/v1/standup/today  — cached or generate
   - POST /api/v1/standup/generate  — force regenerate
   - GET /api/v1/standup/history  — last 7

Use @llm_retry(max_retries=3) on the LLM call.
Use Prompts.STANDUP_SYSTEM and Prompts.STANDUP_USER from app.lib.prompts.
Reference: AI_ARCHITECTURE.md Section 7.
```

```bash
# Test standup generation
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pm@pilotpm.demo","password":"pilotpm2026"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/api/v1/standup/generate \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**F-001 Acceptance Criteria (PRD.md):**
- [ ] Digest includes entry for every engineer (Sarah, Tom, Mike)
- [ ] Each entry has: did, working_on, status (on_track/blocked/check_in), sources
- [ ] Sarah shows "blocked" status (PR #143 stale, Slack "waiting on keys")
- [ ] Mike shows "check_in" status (0 commits 24hrs)
- [ ] Generated in < 60 seconds
- [ ] `GET /today` returns cached version on second call
- [ ] `POST /generate` with GitHub down returns partial digest with warning

---

### Step 3.2 — F-002: Blocker Radar (P1)

**Reference**: PRD.md F-002, AI_ARCHITECTURE.md Section 7 (blocker_agent), BACKEND_STRUCTURE.md Section 10

**AI Agent Prompt:**
```
Implement the blocker workflow for PilotPM — F-002.

1. app/repositories/blocker_repo.py
   - BaseRepository subclass, collection="blockers"
   - find_active() -> list — status="active"
   - find_resolved(days=7) -> list
   - find_by_id(id) -> dict | None
   - insert(blocker) -> dict
   - update_status(id, status, dismissed_reason) -> dict

2. app/services/blocker_service.py
   Reference: BACKEND_STRUCTURE.md Section 10 exactly.
   Implement:
   - get_active_blockers(db) -> list
   - get_resolved(days, db) -> list
   - dismiss(blocker_id, reason, db) -> dict | None
   - run_blocker_scan(db) -> list  — full pipeline:
     a. Fetch pr_data, slack_data, ticket_data in parallel (asyncio.gather)
     b. Sanitize inputs via InputGuardrails
     c. call_ai with BLOCKER_SYSTEM + BLOCKER_USER, temperature=0.1
     d. Parse JSON, deduplicate against existing active blockers
     e. For each new blocker: insert to MongoDB + stage Slack ping in review queue
     f. Return all active blockers

3. app/api/v1/blockers.py
   Reference: BACKEND_STRUCTURE.md Section 9 exactly.
   All 4 endpoints.

4. app/jobs/blocker_job.py
   run_blocker_job() — calls run_blocker_scan() every 15 min during work hours.
```

**F-002 Acceptance Criteria (PRD.md):**
- [ ] PR #143 (open 52hrs, 0 reviews) detected as critical blocker
- [ ] Sarah's "waiting on keys" Slack message detected as blocker
- [ ] Mike's 0 commits → "watch" flag
- [ ] All 3 seeded blockers detected in < 10 seconds
- [ ] `PATCH /dismiss` removes blocker from active list
- [ ] Dismissed blocker appears in `/history`
- [ ] `0` false positives on clean demo data

---

### Step 3.3 — F-003: Sprint Autopilot (P2)

**Reference**: PRD.md F-003, AI_ARCHITECTURE.md Section 7 (sprint_agent), Prompts.SPRINT_SYSTEM

**AI Agent Prompt:**
```
Implement the sprint planning workflow for PilotPM — F-003.

1. app/repositories/sprint_repo.py
   - collection="sprint_plans"
   - find_draft() -> dict | None  — status="draft"
   - find_current() -> dict | None  — status="active"
   - insert(plan) -> dict
   - update(id, data) -> dict
   - get_sprint_number() -> int  — max sprint_number in collection + 1

2. app/services/sprint_service.py
   - get_current_sprint(db) -> dict
   - get_draft(db) -> dict | None
   - generate_draft(db) -> dict:
     a. Pull backlog from MondayService.get_backlog()
     b. Pull velocity from GitHubService.get_velocity_per_engineer(sprints=3)
     c. Pull carry_forward from MondayService.get_incomplete_tickets()
     d. call_ai(task="sprint") → K2 Think V2 with SPRINT_SYSTEM + SPRINT_USER
     e. Parse JSON, validate utilization_pct <= 100
     f. Save as draft in MongoDB
     g. Return draft
   - update_draft_tickets(sprint_id, tickets, db) -> dict  — PM edits
   - approve_sprint(db) -> dict:
     a. Get draft from MongoDB
     b. Validate utilization_pct <= 110 (raise ValueError if over)
     c. Stage monday_sprint action in review queue
     d. Stage calendar_events action in review queue
     e. Return staged actions

3. app/api/v1/sprint.py  — all 5 endpoints from BACKEND_STRUCTURE.md §8
```

**F-003 Acceptance Criteria (PRD.md):**
- [ ] 20 backlog tickets → scored draft in < 90 seconds
- [ ] Each ticket has: score (1–100), reasoning (1 sentence), assigned_to, estimated_pts
- [ ] Draft capacity ≤ 100% (no over-assignment)
- [ ] `PATCH /draft/tickets` — uncheck a ticket → capacity bar updates
- [ ] `POST /approve` with utilization > 110% → 400 error with clear message
- [ ] On approval → two actions staged in review queue (monday_sprint + calendar_events)
- [ ] K2 Think V2 shown in agent reasoning trail

---

### Step 3.4 — F-004: Auto Status Reports (P3)

**Reference**: PRD.md F-004, AI_ARCHITECTURE.md Prompts.REPORT_SYSTEM

**AI Agent Prompt:**
```
Implement the status report workflow for PilotPM — F-004.

1. app/repositories/report_repo.py
   - collection="status_reports"
   - find_current_week() -> dict | None
   - find_history(n=4) -> list
   - insert(report) -> dict
   - update(id, data) -> dict

2. app/integrations/hex_service.py
   - Class HexService
   - generate_sprint_dashboard(sprint_data) -> str  — returns Hex embed URL
   - Use HEX_API_KEY from settings.
   - On failure: return None, log warning.

3. app/integrations/gmail_service.py
   - send_email(to_emails, subject, body) -> bool
   - Use Gmail API or simple SMTP fallback.
   - to_emails from settings.STAKEHOLDER_EMAILS (comma-split).

4. app/services/report_service.py
   - generate_report(db) -> dict:
     a. Pull closed tickets + merged PRs from context snapshot
     b. call_ai(Prompts.REPORT_SYSTEM, REPORT_USER, task="general", temperature=0.4)
     c. Generate Hex dashboard via HexService
     d. Save report draft to MongoDB
     e. Stage gmail_send action in review queue
     f. Return report
   - edit_report(report_id, body, db) -> dict
   - send_report(report_id, db) -> dict:
     a. Check not already sent this week
     b. Stage gmail_send in review queue
     c. Return staged action

5. app/api/v1/reports.py  — all 5 endpoints
6. app/jobs/report_job.py  — Friday 5pm APScheduler trigger
```

**F-004 Acceptance Criteria (PRD.md):**
- [ ] Report generated in < 15 seconds
- [ ] Includes: shipped items (from demo data), PRs merged, blockers resolved
- [ ] Hex dashboard URL embedded in report (or plain text if Hex unavailable)
- [ ] `PATCH /edit` — PM edits body inline, changes persisted
- [ ] `POST /send` with email already sent this week → 400 "Already sent" error
- [ ] Gmail send confirmed (check test inbox)

---

## Phase 4: Voice Agent (7:00pm – 10:00pm, ~3 hours, P3)

### Step 4.1 — ElevenLabs Agent Setup

```bash
# Do this in ElevenLabs dashboard (ui.elevenlabs.io):
# 1. Create new Conversational AI agent
# 2. Agent name: "PilotPM"
# 3. First message: "Hey, this is PilotPM. What do you need to know about the project?"
# 4. Copy the AGENT_ID → paste into .env as ELEVENLABS_AGENT_ID
# 5. System prompt: leave blank — we inject it dynamically per call via webhook
```

### Step 4.2 — Twilio Phone Number

```bash
# 1. Go to twilio.com → sign up (free $15 credit)
# 2. Buy a US phone number (~$1)
# 3. Copy: Account SID, Auth Token, Phone Number → paste into .env
# 4. Leave webhook URL blank for now — we'll set it after ngrok/Railway deploy
```

### Step 4.3 — Voice Service + Webhook

**AI Agent Prompt:**
```
Implement the voice agent for PilotPM — F-005.

1. app/repositories/transcript_repo.py
   - collection="call_transcripts"
   - log_call_start(call_sid, caller, db) -> dict
   - log_call_end(call_sid, duration, db) -> bool
   - find_recent(n=10, db) -> list

2. app/services/voice_service.py
   - get_voice_context(db) -> dict  — calls get_context_for_voice() + adds agent_id
   - get_voice_context_summary(db) -> dict  — for dashboard display
   - log_call_start(call_sid, caller, db) -> dict
   - get_transcripts(limit, db) -> list

3. app/api/v1/voice.py
   Reference: BACKEND_STRUCTURE.md Section 17 exactly.
   - POST /api/v1/voice/webhook/inbound  — Twilio webhook, returns TwiML XML
     Connects call to ElevenLabs via Stream + WebSocket
     Injects current voice context into ElevenLabs system prompt
   - GET /api/v1/voice/context  — dashboard display
   - GET /api/v1/voice/transcripts  — last 10 calls

4. app/jobs/scheduler.py
   Reference: BACKEND_STRUCTURE.md Section 15.
   Add all 4 APScheduler jobs:
   - context_refresh: every 15 minutes
   - daily_standup: 9am ET daily
   - blocker_poll: every 15min, 8am-8pm ET
   - weekly_report: Friday 5pm ET
```

### Step 4.4 — Deploy Backend + Wire Twilio

```bash
# Option A: Railway (recommended — free tier, takes 5 mins)
npm install -g @railway/cli
railway login && railway init
railway up
railway variables set \
  MONGODB_URI="..." \
  LAVA_API_KEY="..." \
  K2_API_KEY="..." \
  GITHUB_TOKEN="..." \
  SLACK_BOT_TOKEN="..." \
  MONDAY_API_KEY="..." \
  ELEVENLABS_API_KEY="..." \
  ELEVENLABS_AGENT_ID="..." \
  TWILIO_ACCOUNT_SID="..." \
  TWILIO_AUTH_TOKEN="..." \
  TWILIO_PHONE="..." \
  HEX_API_KEY="..." \
  DEMO_EMAIL="pm@pilotpm.demo" \
  DEMO_PASSWORD="pilotpm2026" \
  JWT_SECRET="..." \
  ENV="production"

# Get your Railway URL (e.g. https://pilotpm-production.up.railway.app)
RAILWAY_URL=$(railway status --json | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

# Wire Twilio webhook:
# Go to twilio.com → Phone Numbers → your number → Voice Webhook
# Set to: https://[railway-url]/api/v1/voice/webhook/inbound
# Method: HTTP POST
```

```bash
# Test the phone call:
# 1. Call your Twilio number from any phone
# 2. Should hear ElevenLabs voice: "Hey, this is PilotPM..."
# 3. Ask: "What's blocking my team?"
# 4. Should answer with Sarah/Tom/Mike blocker data
```

**F-005 Acceptance Criteria (PRD.md):**
- [ ] Calling Twilio number connects within 2 rings
- [ ] ElevenLabs voice answers: "Hey, this is PilotPM..."
- [ ] "What's blocking my team?" → correct answer with engineer names
- [ ] "Give me sprint summary" → current sprint data
- [ ] "How is Sarah doing?" → Sarah's standup card data
- [ ] Response spoken in < 3 seconds
- [ ] Transcript logged to MongoDB after call ends

---

## Phase 5: Review Queue (10:00pm – 11:00pm, ~1 hour, P1)

### Step 5.1 — Review Service + Endpoints

**AI Agent Prompt:**
```
Implement the review queue for PilotPM — F-011.

1. app/repositories/review_repo.py
   Reference: BACKEND_STRUCTURE.md Section 11 (ReviewRepository).
   - collection="review_queue"
   - find_pending() -> list
   - find_by_id(id) -> dict | None
   - insert(action) -> dict
   - update_status(id, status, result) -> dict
   - count_pending() -> int

2. app/services/review_service.py
   - stage_action(action_type, title, description, data, reasoning, workflow, db) -> dict
     Creates ReviewAction with status="pending", saves to MongoDB
   - approve_action(action_id, db) -> dict:
     Gets action, executes it based on type:
       "slack_message" → SlackService.post_message or send_dm
       "monday_sprint" → MondayService.create_board
       "calendar_event" → CalendarService.create_event
       "gmail_send" → GmailService.send_email
     Updates status to "executed" or "failed"
   - approve_batch(action_ids, db) -> list  — execute all in parallel
   - reject_action(action_id, reason, db) -> dict  — status="rejected", log reason
   - edit_action(action_id, content, db) -> dict  — update action.data

3. app/api/v1/review.py  — all 6 endpoints from BACKEND_STRUCTURE.md §8

CRITICAL: review_service.stage_action() must be imported and called by
standup_service, blocker_service, sprint_service, and report_service.
Nothing executes without going through the review queue first.
```

**Checklist:**
- [ ] All workflow actions appear in `GET /api/v1/review` after triggering
- [ ] `POST /approve` executes the action (check Slack/Monday.com)
- [ ] `POST /reject` with reason logs to MongoDB
- [ ] `PATCH /edit` changes action content before execution
- [ ] `GET /count` returns correct badge count
- [ ] 0 actions execute automatically without approval

---

## Phase 6: Frontend (11:00pm – 3:00am, ~4 hours, P4)

### Step 6.1 — Scaffold with Lovable

```
Go to lovable.dev (or v0.dev as fallback)

Paste this prompt:
"Build a React dashboard called PilotPM — an AI project management tool.
Dark sidebar with these nav items: Dashboard, Standup Feed, Blocker Radar,
Sprint Planner, Status Reports, Backlog AI, Voice Agent, Review Queue (with badge count).
Purple (#534AB7) accent color. Clean flat design, white cards with 0.5px borders.
Each page has loading skeleton, populated, and empty states.
The review queue page has approve/reject/edit buttons per action card.
Use Tailwind CSS. Export as a React project."

Download the zip, add to pilotpm/frontend/
cd frontend && npm install
```

### Step 6.2 — Wire Frontend to Backend

**AI Agent Prompt:**
```
Wire the PilotPM React frontend to the FastAPI backend.
Backend URL: [your Railway URL]
Auth: POST /auth/login → store JWT in localStorage → add Authorization: Bearer header to all requests.

Wire these pages to these endpoints (reference APP_FLOW.md Section 5):
- Dashboard → GET /api/v1/standup/today + GET /api/v1/blockers
- Standup Feed → GET /api/v1/standup/today, POST /api/v1/standup/generate
- Blocker Radar → GET /api/v1/blockers, POST /api/v1/blockers/scan, PATCH /api/v1/blockers/{id}/dismiss
- Sprint Planner → GET /api/v1/sprint/draft, POST /api/v1/sprint/draft/generate, POST /api/v1/sprint/approve
- Status Reports → GET /api/v1/reports/current, POST /api/v1/reports/generate, POST /api/v1/reports/{id}/send
- Voice Agent → GET /api/v1/voice/context, GET /api/v1/voice/transcripts
- Review Queue → GET /api/v1/review, POST /api/v1/review/{id}/approve, POST /api/v1/review/approve-batch, POST /api/v1/review/{id}/reject

Add error states per APP_FLOW.md Section 7 exact error copy strings.
Review queue badge: poll GET /api/v1/review/count every 30 seconds.
```

```bash
# Deploy frontend to Vercel
npx vercel --prod
# Set env var: VITE_API_URL=https://[railway-url]
```

**Checklist:**
- [ ] Login page works with demo credentials
- [ ] Dashboard shows today's AI digest
- [ ] Blocker page shows 3 seeded blockers with severity badges
- [ ] Sprint planner shows scored tickets, capacity bar updates on uncheck
- [ ] Review queue badge shows count, actions approve/reject correctly
- [ ] Voice page shows phone number + last transcript

---

## Phase 7: Integration + Polish (3:00am – 7:00am, ~4 hours)

### Step 7.1 — End-to-End Tests

```bash
# Run all 5 workflows end-to-end with demo data
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"pm@pilotpm.demo","password":"pilotpm2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "=== F-001: Standup ==="
curl -s -X POST "http://localhost:8000/api/v1/standup/generate" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
engineers = d.get('digest', [])
print(f'Engineers: {[e[\"engineer\"] for e in engineers]}')
print(f'Statuses: {[e[\"status\"] for e in engineers]}')
"

echo "=== F-002: Blockers ==="
curl -s -X POST "http://localhost:8000/api/v1/blockers/scan" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
blockers = json.load(sys.stdin)
print(f'Blockers found: {len(blockers)}')
for b in blockers: print(f'  [{b[\"severity\"]}] {b[\"engineer\"]}: {b[\"description\"][:60]}')
"

echo "=== F-003: Sprint ==="
curl -s -X POST "http://localhost:8000/api/v1/sprint/draft/generate" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
tickets = d.get('tickets', [])
print(f'Tickets scored: {len(tickets)}, Capacity: {d.get(\"utilization_pct\")}%')
print(f'Top ticket: {tickets[0][\"name\"]} (score: {tickets[0][\"score\"]})')
"

echo "=== F-004: Reports ==="
curl -s -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f'Report: {r.get(\"subject\", \"generated\")}')
print(f'Hex dashboard: {\"yes\" if r.get(\"hex_url\") else \"no\"}')
"

echo "=== Review Queue ==="
curl -s "http://localhost:8000/api/v1/review" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
actions = json.load(sys.stdin)
print(f'Pending actions: {len(actions)}')
for a in actions: print(f'  [{a[\"type\"]}] {a[\"title\"]}')
"
```

### Step 7.2 — Fallback Testing

```bash
# Test Lava + optional Gemini (temporarily break Lava key)
# 1. Set LAVA_API_KEY=invalid in .env; keep GEMINI_API_KEY valid
# 2. Restart server
# 3. Run standup generate — should hit Gemini direct if configured
# 4. Check logs for "lava_primary.failed" / "lava_fallback.failed" + "llm.using_gemini_direct_fallback"
# 5. Restore correct LAVA_API_KEY

# Test K2 fallback
# 1. Set K2_API_KEY=invalid
# 2. Run sprint generate — should fall back to Lava chain (then optional Gemini)
# 3. Check logs for "k2.failed" + "falling_back_to=lava_primary"
# 4. Restore correct key
```

---

## Phase 8: Devpost + Demo Assets (7:00am – 9:00am, ~2 hours)

### Step 8.1 — Google Veo Video

```
Prompt for Google Veo (veo.google.com or via Vertex AI):
"A 45-second product demo video of PilotPM, an AI project management tool.
Scene 1 (0-10s): A tired PM looks at a calendar full of standup meetings — they all disappear.
Scene 2 (10-20s): A sleek dark dashboard appears showing engineer status cards with green/red badges.
Scene 3 (20-30s): A phone rings — someone answers — an AI voice says 'You have 3 blockers...'
Scene 4 (30-40s): A sprint board auto-fills with tickets in 3 seconds.
Scene 5 (40-45s): Text: 'PilotPM — No standups. No missed blockers. No manual reports.'
Style: Modern SaaS product demo, clean animations, dark UI."
```

### Step 8.2 — Google Stitch Images

```
Generate these 5 images in Google Stitch for landing page:
1. Hero: "PilotPM dashboard on laptop screen, dark UI, purple accents, engineering team context"
2. Standup: "AI-generated standup cards showing engineer status, green on track, red blocked"
3. Sprint: "Kanban sprint board with AI scores and auto-assignment, purple theme"
4. Voice: "Smartphone showing incoming call with AI assistant, PilotPM logo"
5. Reports: "Analytics dashboard with sprint velocity charts, stakeholder email draft"
```

### Step 8.3 — Devpost Submission

```
Title: PilotPM — AI PM Orchestrator for Software Teams

Tagline: No standups. No missed blockers. No manual reports.

Description template:
"We built PilotPM in 24 hours at YHack 2026.
PilotPM watches your GitHub, Slack, and Monday.com 24/7 and runs your sprint automatically.

What it does:
• Auto-generates daily standup digests from real commit + Slack data
• Detects blockers before anyone reports them (stale PRs, blocking Slack messages, inactivity)
• Plans sprints using MBZUAI K2 Think V2's multi-step reasoning
• Writes and sends weekly stakeholder reports via Gmail
• Answers your questions on a REAL PHONE CALL — powered by ElevenLabs + Twilio

Tech: FastAPI + MongoDB + LangGraph + Lava forward (OpenAI via gateway) + optional Gemini fallback + K2 Think V2 + ElevenLabs + Twilio + React

Prizes targeting: Harper (Personal AI Agents), Hex API, MBZUAI K2, Lava, Zed, ElevenLabs MLH"

Tracks to select:
✅ Personal AI Agents (Harper)
✅ Built with Zed
✅ Best use of Hex API
✅ Best use of K2 Think V2
✅ Best use of Lava API
✅ ElevenLabs MLH
✅ MongoDB MLH
✅ Best UI/UX
```

---

## Phase 9: Pre-Demo Checklist (9:00am – 10:00am)

Run this checklist in order. Don't skip anything.

```
=== BACKEND ===
□ GET /health returns {"status":"ok","gemini_via_lava":true,"mongo":true} (field name is legacy; LLM path uses Lava forward + OpenAI upstream)
□ POST /auth/login returns valid JWT
□ Lava forward works (official host https://api.lava.so — see Lava quickstart / project smoke test)
□ K2 Think V2 responds: POST to K2 base with test message → response in <10s
□ GitHub token valid: curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
□ Slack bot can read #engineering: check SlackService.get_recent_messages()
□ MongoDB Atlas shows collections with demo data seeded

=== WORKFLOWS ===
□ F-001: POST /standup/generate → 3 engineer cards, Sarah=blocked, Mike=check_in
□ F-002: POST /blockers/scan → 3 blockers detected, PR #143 critical
□ F-003: POST /sprint/draft/generate → scored tickets, capacity ≤ 100%
□ F-004: POST /reports/generate → report with Hex URL
□ F-011: GET /review → actions from above workflows in queue
□ POST /review/{id}/approve → executes action (verify in Slack/Monday.com)

=== VOICE ===
□ Call Twilio number → ElevenLabs answers within 2 rings
□ Ask "What's blocking my team?" → correct answer with engineer names
□ Ask "Sprint summary" → correct sprint data
□ Call transcript appears in GET /voice/transcripts

=== FRONTEND ===
□ Login works → redirects to dashboard
□ Dashboard shows standup digest
□ Blocker radar shows 3 cards with severity badges
□ Sprint planner shows scored draft, capacity bar reacts to checkbox
□ Review queue badge shows correct count
□ Approve action from queue → visible confirmation

=== DEMO REHEARSAL ===
□ Run full 90-second demo script 3 times
□ Time each section: standup(20s), blockers(15s), sprint(15s), voice(25s), reports(15s)
□ Practice handing phone to judge and saying "ask it anything"
□ Verify fallback: disconnect internet briefly → toast appears, cached data shown
```

---

## Phase 10: Demo Script (90 seconds)

```
[0:00] Open dashboard
  "This is what your PM sees every morning instead of a 30-minute standup.
   Sarah is blocked, Tom is on track, Mike needs a check-in.
   The AI read 12 commits, 34 Slack messages, and 8 ticket updates."

[0:20] Click Blocker Radar
  "3 blockers. Nobody filed a ticket.
   PR #143 open 52 hours with zero reviews.
   Tom's Slack message 'waiting on keys' auto-detected."
  Click "Ping @mike" → review queue opens → approve
  "That ping just went to Slack."

[0:40] Click Sprint Planner
  "K2 Think V2 — a 70B reasoning model from MBZUAI —
   scored 20 backlog tickets in 14 seconds.
   Payment gateway is #1: blocks Q2 revenue, Tom can ship in 3 days."
  Click Approve → "Sprint 25 pushed to Monday.com."

[0:55] Hand phone to judge
  "Call this number."
  Judge dials +1 (203) 555-PILOT
  Judge asks: "What's blocking my team?"
  AI answers: "You have 3 blockers. Sarah has been waiting on API keys
   from Mike for 2 days. Tom has 5 PRs waiting for review..."
  [entire room should be silent]

[1:20] Click Status Reports
  "Friday report. Written automatically.
   PM never typed a single word."

[1:30] Close
  "PilotPM routes general AI through the Lava gateway (OpenAI-compatible models),
   K2 Think V2 for sprint reasoning, optional Gemini if Lava fails, and ElevenLabs for voice.
   One PM. Five engineers. Zero standups."
```

---

## Appendix A: AI Agent Prompts Master List

Use these exact prompts with Cursor / Claude Code. Copy-paste, don't paraphrase.

```
# For any implementation task:
"You are building PilotPM. Read [DOC.md] Section [N].
Implement [component] exactly as specified.
Stack: Python 3.11, FastAPI, Motor (MongoDB), LangGraph, APScheduler.
No SQLModel. No Alembic. No pip. Use uv.
File: app/[path]. Do not add features not in the spec."

# When stuck on integration:
"The PilotPM [service] is failing because [error].
The spec is in [DOC.md] Section [N].
The data model is [describe].
Fix only this specific issue. Do not refactor other files."

# For a complete feature slice:
"Implement PilotPM feature [F-00X] as a complete vertical slice.
1. Repository: app/repositories/[name]_repo.py
2. Service: app/services/[name]_service.py
3. Router: app/api/v1/[name].py
Reference: BACKEND_STRUCTURE.md Sections 9, 10, 11.
All prompts come from app/lib/prompts.py Prompts class — never inline.
All LLM calls use call_ai() from app/lib/llm.py — never call Lava directly."
```

---

## Appendix B: Common Failures & Fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `LLM returns invalid JSON` | Gemini added markdown fences | Strip with `re.sub(r'```(?:json)?\s*', '', raw)` |
| `MongoDB connection timeout` | Atlas IP whitelist | Add `0.0.0.0/0` to Atlas Network Access |
| `Twilio webhook 403` | Twilio signature validation | Disable validation for hackathon, re-enable later |
| `ElevenLabs no audio` | Wrong audio format | Set μ-law 8kHz in ElevenLabs agent settings |
| `K2 timeout > 60s` | Large sprint backlog | Reduce to 15 tickets for demo, increase timeout to 90s |
| `Slack 429 rate limit` | Too many reads | Add `asyncio.sleep(1)` between calls |
| `Review queue action fails` | Monday.com API error | Log error, set action status to "failed", show retry button |
| `Frontend CORS error` | Missing origin in settings | Add Vercel URL to `CORS_ORIGINS` in settings |
| `JWT expired during demo` | 8hr token expired | Set `JWT_EXPIRE_MINUTES=1440` for demo day |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | March 28, 2026 | Aman | Initial — all 10 phases, PilotPM-specific |
