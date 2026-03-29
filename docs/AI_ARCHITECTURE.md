# AI_ARCHITECTURE.md — AI/ML System Design

> **Version**: 1.1 | **Last Updated**: March 29, 2026
> **Project**: PilotPM
> **References**: PRD.md v1.0, APP_FLOW.md v1.0
> **Stack**: Python + FastAPI + LangGraph + Lava forward proxy + K2 Think V2 + optional Gemini (google-genai)

---

## 1. System Overview

**Type**: Multi-agent pipeline with LangGraph orchestration
**AI goal**: Watch GitHub, Slack, and Monday.com continuously — automatically generate standups, detect blockers, plan sprints, write reports, and answer voice calls — with human approval before execution
**Critical path**: Yes — AI failure breaks all 5 P0 features. Fallback chain required for every model call.

### Primary Inference Stack

```
General LLM:  OpenAI-compatible models via Lava forward (api.lava.so → /v1/forward?u=OpenAI chat/completions)
              Primary: LAVA_MODEL_PRIMARY (default gpt-4o-mini) → fallback: LAVA_MODEL_FALLBACK (default gpt-4o)
Last resort:  Google Gemini via google-genai + GEMINI_API_KEY (only if both Lava calls fail)
Reasoning:    MBZUAI K2 Think V2 direct API (sprint + backlog tasks — sponsor)
Voice:        ElevenLabs Conversational AI (STT + TTS, Twilio bridge)
```

See `app/lib/llm.py` and `app/config.py` for exact env vars (`LAVA_*`, `GEMINI_*`, `K2_*`).

### Architecture Diagram

```
INPUTS (GitHub API / Slack API / Monday.com MCP / Gmail MCP)
    |
    v
[DataCollector]              <- fetch + normalize from all sources
    |
    v
[ContextBuilder]             <- assemble project context snapshot
    |                           stored in MongoDB, refreshed every 15 mins
    v
[LangGraphOrchestrator]      <- route to correct workflow agent
    |
    +---> [StandupAgent]     <- F-001: digest from commits + Slack + tickets
    |
    +---> [BlockerAgent]     <- F-002: detect + classify + draft pings
    |
    +---> [SprintAgent]      <- F-003: score + assign + capacity-check
    |
    +---> [ReportAgent]      <- F-004: compile + draft + Hex chart
    |
    +---> [VoiceAgent]       <- F-005: ElevenLabs context injection
    |
    +---> [BacklogAgent]     <- F-010: score + rank + matrix (P1)
    |
    v
[ReviewQueue]                <- all actions staged here, no auto-execute
    |
    v
[HumanApproval]              <- PM approves / edits / rejects
    |
    v
[ActionExecutor]             <- Slack / Monday.com / Gmail / Calendar MCPs
```

### Model Routing

```
REQUEST ARRIVES (call_ai)
    |
    ├── task = "sprint" or "backlog"
    │   └── K2 Think V2 (MBZUAI direct API)
    │       └── IF K2 fails → same chain below
    │
    └── Lava: POST {LAVA_BASE}/v1/forward?u={LAVA_FORWARD_UPSTREAM}
        │   Bearer LAVA_API_KEY — OpenAI-style body (model + messages)
        ├── 1) LAVA_MODEL_PRIMARY
        ├── 2) LAVA_MODEL_FALLBACK (if 1 fails)
        └── 3) IF GEMINI_API_KEY set and both Lava calls failed → Gemini (google-genai, GEMINI_MODEL)
```

---

## 2. Model Registry

> Defaults live in `app/config.py`; override via `.env`. Avoid un-pinned `"latest"` IDs in production.

| ID | Model (default) | Provider | How Accessed | Purpose | Notes |
|----|-----------------|----------|----------------|---------|--------|
| M-01 | gpt-4o-mini | OpenAI (via **Lava forward**) | `LAVA_API_KEY` | Primary general LLM — standup, blockers, reports, classify | `LAVA_FORWARD_UPSTREAM` must match upstream API |
| M-02 | gpt-4o | OpenAI (via **Lava forward**) | `LAVA_API_KEY` | Second Lava attempt if primary errors | `LAVA_MODEL_FALLBACK` |
| M-03 | gemini-3-flash-preview (configurable) | **Google Gemini** direct | `GEMINI_API_KEY` | Last resort if **both** Lava calls fail | `google-genai` SDK; set `GEMINI_MODEL` to pin |
| M-04 | MBZUAI-IFM/K2-Think-v2 | **MBZUAI** direct | `K2_API_KEY` | Sprint + backlog tasks | Not Lava |
| M-05 | ElevenLabs Conversational AI | ElevenLabs | WebSocket + Twilio | Voice agent STT/TTS | Not REST LLM |

> **Note**: General traffic is billed/routed through **Lava** (one merchant secret). **K2** and **ElevenLabs** use their own keys. **Gemini** is optional and only used when Lava cannot complete the request.

### Model Selection Rationale

| Task | Chosen path | Reason |
|------|-------------|--------|
| Standup / blockers / reports / classify | M-01 → M-02 (Lava, OpenAI upstream) | Single Lava key; OpenAI chat models match `LAVA_FORWARD_UPSTREAM`; two attempts before optional Gemini |
| Sprint + backlog `task` | M-04 (K2 direct) | Sponsor reasoning model; falls through to Lava+Gemini chain if K2 errors |
| Voice | M-05 (ElevenLabs) | Streaming voice; not via Lava REST |
| Last resort | M-03 (Gemini direct) | Only if Lava is unavailable; requires `GEMINI_API_KEY` |

---

## 3. Python Client Setup

**Source of truth:** `app/lib/llm.py` (do not duplicate long snippets here — they drift).

| Function | Role |
|----------|------|
| `call_via_lava` | `httpx` **POST** `{LAVA_BASE}/v1/forward` with `params={"u": LAVA_FORWARD_UPSTREAM}`, **Bearer** `LAVA_API_KEY`, JSON body OpenAI chat format (`model`, `messages`, …). |
| `call_k2` | **POST** `{K2_API_BASE}/v1/chat/completions` with `K2_MODEL` (default `MBZUAI-IFM/K2-Think-v2`), Bearer `K2_API_KEY`. |
| `call_via_gemini` | Optional: **`google-genai`** `Client(api_key=GEMINI_API_KEY).models.generate_content` with `GenerateContentConfig(system_instruction=…)`; runs in `asyncio.to_thread`. |
| `call_ai` | Router: sprint/backlog → K2 (then Lava×2 → Gemini if key set); else Lava primary → Lava fallback → Gemini if key set. |

**Lava docs:** [Forward proxy](https://lava.so/docs/gateway/forward-proxy.md), [Quickstart](https://lava.so/docs/get-started/quickstart-track.md).  
**Gemini docs:** [Libraries](https://ai.google.dev/gemini-api/docs/libraries), [Terms](https://ai.google.dev/gemini-api/terms).

---

## 4. Prompt Registry

> All prompts versioned here. Never write prompts inline in agents or route handlers.

```python
# app/lib/prompts.py
"""
All system prompts for PilotPM.
Versioned with metadata comments.
Temperature and max_tokens recommendations included per prompt.
"""


class Prompts:

    # ── PROMPT-001: Input Classifier ──────────────────────────────────────────
    # v1.0 | Model: M-01 (Gemini 2.0 Flash 35B) | Temp: 0.0 | Max tokens: 50
    # Used by: LangGraphOrchestrator to route inputs to correct workflow agent
    CLASSIFIER_SYSTEM = """
You are a software project management classifier.
Classify the input into EXACTLY ONE category:

standup     - question or request about what engineers worked on today/yesterday
blocker     - something is blocked, stalled PR, engineer not responding, dependencies missing
sprint      - sprint planning, backlog grooming, ticket assignment, velocity
report      - status update, stakeholder report, weekly summary, what shipped
backlog     - prioritizing tickets, ranking work, what to build next
voice       - a voice query about project status (usually short, conversational)
unknown     - none of the above

Respond with ONLY the category name. No explanation. No punctuation.
"""

    CLASSIFIER_USER = "Input: {input}"

    # ── PROMPT-002: Standup Digest Synthesis ──────────────────────────────────
    # v1.0 | Model: M-02 (Gemini 2.0 Flash 122B) | Temp: 0.3 | Max tokens: 3000
    # Used by: StandupAgent (F-001)
    STANDUP_SYSTEM = """
You are PilotPM's standup agent. You synthesize raw engineering activity data
into a clear, concise daily digest for the PM — without requiring any input
from engineers.

Your output replaces the morning standup meeting entirely.

Rules:
- Write in third person (e.g. "Sarah merged..." not "I merged...")
- Include ONLY facts you can cite from the provided data
- If you cannot confirm something, say "unknown" — never fabricate
- Every claim must reference its source (GitHub, Slack, or Monday.com)
- Flag engineers with no activity in 24 hours as "Check in"
- Flag engineers with explicit blocking signals as "Blocked"
- Keep each engineer summary to 3-5 sentences maximum
- Do NOT include implementation details or code specifics
- Output valid JSON matching the schema exactly

Output format (JSON):
{
  "generated_at": "ISO timestamp",
  "digest": [
    {
      "engineer": "name",
      "status": "on_track|blocked|check_in",
      "did": "what they completed (cited)",
      "working_on": "current focus",
      "blocker": "description or null",
      "sources": ["GitHub: 4 commits", "Slack: 1 message", "Monday: 2 updates"]
    }
  ],
  "summary": "1-sentence team summary",
  "data_gaps": ["list of unavailable sources, empty if all available"]
}
"""

    STANDUP_USER = """
Time window: last 24 hours ending {timestamp}
Team: {team_names}

GitHub activity:
{github_data}

Slack messages (#engineering, #general):
{slack_data}

Monday.com ticket updates:
{monday_data}

Generate the standup digest JSON.
"""

    # ── PROMPT-003: Blocker Detection & Classification ─────────────────────────
    # v1.0 | Model: M-02 (Gemini 2.0 Flash 122B) | Temp: 0.1 | Max tokens: 2000
    # Used by: BlockerAgent (F-002)
    BLOCKER_SYSTEM = """
You are PilotPM's blocker detection agent. Analyze the provided signals and
identify genuine blockers — things that are actively preventing an engineer
from making progress.

Severity levels:
- critical: work is completely stopped, SLA at risk, dependency missing
- medium: slowing progress but workarounds exist
- watch: no activity detected, may or may not be blocked

For each blocker, draft a natural Slack ping to the person who can unblock it.
The ping should be friendly, specific, and under 2 sentences.

Rules:
- Only flag genuine blockers, not normal work pace
- A PR open for 48hrs with 0 reviews is ALWAYS critical
- "Blocked", "waiting on", "can't proceed", "stuck" in Slack = blocker signal
- 0 commits for 24+ hours = watch flag (not auto-critical)
- Do NOT flag engineers who are clearly in deep focus (many commits, no Slack)
- Output valid JSON matching the schema exactly

Output format (JSON):
{
  "blockers": [
    {
      "id": "unique string",
      "engineer": "name",
      "severity": "critical|medium|watch",
      "type": "pr_stale|slack_signal|inactivity|dependency_missing",
      "description": "clear description of what is blocked and why",
      "blocked_for": "duration string e.g. '2 days'",
      "evidence": "the specific signal that triggered this (PR URL, Slack quote, etc.)",
      "resolver": "name of person who can unblock",
      "draft_ping": "Hey @resolver — brief friendly message asking them to unblock"
    }
  ]
}
"""

    BLOCKER_USER = """
Current time: {timestamp}
Engineers: {team_names}

Open PRs (age + review status):
{pr_data}

Slack messages (last 48 hours):
{slack_data}

GitHub commit activity (last 24 hours, per engineer):
{commit_activity}

Monday.com in-progress tickets (days in status):
{ticket_activity}

Identify all blockers and output JSON.
"""

    # ── PROMPT-004: Sprint Planning (K2 Think V2) ─────────────────────────────
    # v1.0 | Model: M-03 (K2 Think V2) | Temp: 0.0 | Max tokens: 8192
    # Used by: SprintAgent (F-003)
    # NOTE: K2 Think V2 is a reasoning model — keep temp at 0.0
    SPRINT_SYSTEM = """
You are PilotPM's sprint planning agent. Your job is to take a backlog of tickets
and produce an optimal sprint plan — tickets scored, assigned, and capacity-checked.

Scoring methodology (1–100):
- Impact (0–50 pts): Does it unblock other tickets? Does it affect users directly?
  Is it on the critical path for a milestone?
- Effort (0–50 pts, inverse): Low effort = high score. Estimate from description.
  Adjust if engineer velocity data suggests expertise match.
- Bonus: Add 10 pts if ticket has been deferred from previous sprints
- Penalty: Subtract 10 pts if ticket has external dependencies not yet resolved

Assignment rules:
1. Match ticket domain to engineer's recent GitHub activity domains
2. Do not exceed each engineer's velocity capacity
3. P1 tickets must be assigned before P2/P3
4. Leave 10% capacity buffer for unplanned work

Think step by step through each ticket before scoring.
Show your reasoning for each score.

Output valid JSON matching the schema exactly.

Output format (JSON):
{
  "sprint_name": "Sprint {number}",
  "total_capacity_pts": number,
  "used_capacity_pts": number,
  "utilization_pct": number,
  "tickets": [
    {
      "id": "ticket id",
      "name": "ticket name",
      "score": number,
      "reasoning": "1-2 sentence explanation of score",
      "estimated_pts": number,
      "assigned_to": "engineer name",
      "assignment_reason": "why this engineer",
      "priority": "P1|P2|P3",
      "selected": true
    }
  ],
  "deferred": [
    {
      "id": "ticket id",
      "name": "ticket name",
      "reason": "why deferred (capacity / dependency / low priority)"
    }
  ]
}
"""

    SPRINT_USER = """
Sprint number: {sprint_number}
Sprint duration: {sprint_days} days

Team velocity (last 3 sprints average, story points):
{velocity_data}

Backlog tickets:
{backlog_tickets}

Previous sprint incomplete tickets (carry-forward):
{carry_forward}

Score and plan the sprint. Think through each ticket carefully before scoring.
"""

    # ── PROMPT-005: Status Report Writer ──────────────────────────────────────
    # v1.0 | Model: M-02 (Gemini 2.0 Flash 122B) | Temp: 0.4 | Max tokens: 1500
    # Used by: ReportAgent (F-004)
    REPORT_SYSTEM = """
You are PilotPM's status report writer. You compile engineering activity data
into a clear, professional weekly stakeholder update.

The audience is non-technical stakeholders (founders, investors, board members).
Translate technical work into business outcomes wherever possible.

Rules:
- Lead with business impact, not technical details
- "Fixed auth token refresh bug" → "Resolved security vulnerability affecting 2,400 users"
- Keep the email under 200 words
- Use bullet points for shipped items, not paragraphs
- Be honest about blockers — stakeholders should know
- Do NOT include internal drama, engineer names, or blame language
- Output the email body only — no subject line (provided separately)

Output plain text (not JSON, not markdown).
"""

    REPORT_USER = """
Week ending: {week_end_date}
Sprint: {sprint_name} | Days remaining: {days_remaining}

Closed tickets this week:
{closed_tickets}

Merged PRs this week:
{merged_prs}

Blockers resolved:
{resolved_blockers}

Active blockers (ongoing):
{active_blockers}

Next week priorities (top 3 from sprint board):
{next_week_tickets}

Write the stakeholder update email body.
"""

    # ── PROMPT-006: Backlog Prioritization (K2 Think V2) ──────────────────────
    # v1.0 | Model: M-03 (K2 Think V2) | Temp: 0.0 | Max tokens: 6000
    # Used by: BacklogAgent (F-010, P1)
    BACKLOG_SYSTEM = """
You are PilotPM's backlog prioritization agent. Score and rank every ticket
using the ICE framework: Impact × Confidence × Ease.

ICE scoring (each 1–10):
- Impact: How much will this move the needle for users or the business?
  Cross-reference with GitHub issue frequency and Slack complaints.
- Confidence: How confident are we this will have the stated impact?
- Ease: How easy is it to implement? (10 = very easy, 1 = very hard)

Final score = Impact × Confidence × Ease (max 1000)

Think through each ticket carefully. Show reasoning.
Consider dependencies — if ticket A blocks tickets B and C, A gets impact bonus.

Output valid JSON.

Output format (JSON):
{
  "ranked_tickets": [
    {
      "id": "ticket id",
      "name": "ticket name",
      "impact": number,
      "confidence": number,
      "ease": number,
      "ice_score": number,
      "reasoning": "2-3 sentence explanation",
      "dependencies_unblocked": ["list of ticket ids this unblocks"],
      "user_signal": "Slack mentions or GitHub issues referencing this",
      "recommended_sprint": "Sprint N or Backlog"
    }
  ]
}
"""

    BACKLOG_USER = """
Full backlog:
{backlog_tickets}

GitHub issues (by frequency / comments):
{github_issues}

Slack mentions of features/bugs (last 30 days):
{slack_signals}

Score and rank all tickets using ICE framework.
"""

    # ── PROMPT-007: Voice Agent Context Injection ──────────────────────────────
    # v1.0 | Model: M-05 (ElevenLabs Conversational AI) | Temp: N/A (streaming)
    # Used by: VoiceAgent (F-005) — injected as ElevenLabs system prompt
    VOICE_SYSTEM = """
You are PilotPM, an AI project management agent for a software startup.
You answer questions about the engineering team's current status over the phone.

Personality: Professional, concise, friendly. Like a smart EA who knows everything.
Speech style: Natural spoken language. Short sentences. No bullet points (this is voice).
Response length: Under 30 seconds when spoken aloud (~75 words maximum per response).

You have access to real-time data from GitHub, Slack, and Monday.com.
The data below was refreshed at {refresh_timestamp}.

=== CURRENT PROJECT CONTEXT ===

Sprint: {sprint_name} | {days_remaining} days remaining | {velocity_pct}% velocity

Active blockers ({blocker_count}):
{blockers_summary}

Today's standup digest:
{standup_summary}

Recent activity:
{recent_activity}

=== END CONTEXT ===

Rules:
- Answer from the context above — do NOT fabricate
- If data is unavailable, say: "I don't have current data on that — my last update was {refresh_timestamp}"
- If asked to take action (ping someone, create ticket): confirm first, then say "I've noted that for your review"
  — do NOT actually execute actions over the phone
- If asked something outside your scope: "I specialize in project status. I can help with blockers,
  sprint updates, and how specific engineers are doing."
- Keep ALL responses under 75 words

You are a voice assistant. Do not use bullet points, markdown, or lists.
Speak in complete, natural sentences.
"""


# ── Prompt design rules ────────────────────────────────────────────────────────
PROMPT_DESIGN_RULES = """
Temperature guide:
  0.0       classification, scoring, structured JSON output
  0.1–0.3   factual synthesis, report compilation
  0.4–0.6   creative writing, email drafting (Gemini 2.0 Flash recommended 0.6 for thinking mode)
  0.7+      voice agent personality, creative tasks

Always:
  - Specify exact JSON schema in prompt (not just "respond with JSON")
  - Add "Think step by step" for multi-step reasoning (K2 + sprint tasks)
  - Include negative examples: "Do NOT fabricate / Do NOT include..."
  - Never put prompts inline in agents — always use Prompts class
  - Version bump prompts when changing wording (update comment header)
"""
```

---

## 5. Context Builder (RAG-lite)

> PilotPM doesn't use a vector database. Instead it builds a structured context snapshot from live APIs and caches it in MongoDB. The voice agent and all workflow agents consume this snapshot.

```python
# app/services/context_builder.py
"""
Builds and caches the project context snapshot.
Refreshed every 15 minutes via background task.
All agents consume this — no direct API calls from agents.
"""

import asyncio
from datetime import datetime, UTC, timedelta
from app.db.mongo import get_collection
from app.services.github_service import GitHubService
from app.services.slack_service import SlackService
from app.services.monday_service import MondayService
import structlog

log = structlog.get_logger()

CONTEXT_TTL_MINUTES = 15
CONTEXT_COLLECTION = "project_context"


async def build_context_snapshot() -> dict:
    """
    Fetch data from all sources in parallel.
    Returns structured context dict for agent consumption.
    """
    github, slack, monday = await asyncio.gather(
        GitHubService.get_recent_activity(hours=24),
        SlackService.get_recent_messages(hours=24),
        MondayService.get_sprint_status(),
        return_exceptions=True,
    )

    snapshot = {
        "refreshed_at": datetime.now(UTC).isoformat(),
        "github": github if not isinstance(github, Exception) else None,
        "slack": slack if not isinstance(slack, Exception) else None,
        "monday": monday if not isinstance(monday, Exception) else None,
        "sources_available": {
            "github": not isinstance(github, Exception),
            "slack": not isinstance(slack, Exception),
            "monday": not isinstance(monday, Exception),
        },
    }

    # Cache in MongoDB
    col = get_collection(CONTEXT_COLLECTION)
    await col.replace_one({}, {"$set": snapshot}, upsert=True)
    log.info("context.refreshed", sources=snapshot["sources_available"])
    return snapshot


async def get_context_snapshot() -> dict:
    """Get cached context — refresh if stale."""
    col = get_collection(CONTEXT_COLLECTION)
    doc = await col.find_one({})

    if not doc:
        return await build_context_snapshot()

    refreshed_at = datetime.fromisoformat(doc["refreshed_at"])
    age_minutes = (datetime.now(UTC) - refreshed_at).seconds / 60

    if age_minutes > CONTEXT_TTL_MINUTES:
        return await build_context_snapshot()

    return doc


async def get_context_for_voice() -> dict:
    """
    Voice agent needs a condensed context that fits the ElevenLabs system prompt.
    Returns human-readable strings, not raw API data.
    """
    ctx = await get_context_snapshot()
    snapshot = ctx.get("monday", {})

    blockers_summary = _format_blockers_for_voice(ctx)
    standup_summary = _format_standup_for_voice(ctx)
    recent_activity = _format_activity_for_voice(ctx)

    return {
        "refresh_timestamp": ctx["refreshed_at"],
        "sprint_name": snapshot.get("sprint_name", "current sprint"),
        "days_remaining": snapshot.get("days_remaining", "unknown"),
        "velocity_pct": snapshot.get("velocity_pct", "unknown"),
        "blocker_count": len(ctx.get("blockers_cache", [])),
        "blockers_summary": blockers_summary,
        "standup_summary": standup_summary,
        "recent_activity": recent_activity,
    }


def _format_blockers_for_voice(ctx: dict) -> str:
    blockers = ctx.get("blockers_cache", [])
    if not blockers:
        return "No active blockers."
    lines = []
    for b in blockers[:3]:  # max 3 in voice context
        lines.append(f"{b['engineer']} — {b['description']} ({b['blocked_for']})")
    return "\n".join(lines)


def _format_standup_for_voice(ctx: dict) -> str:
    digest = ctx.get("standup_cache", {}).get("digest", [])
    if not digest:
        return "No standup data available."
    lines = []
    for e in digest:
        status_map = {"blocked": "BLOCKED", "check_in": "CHECK IN", "on_track": "on track"}
        status = status_map.get(e["status"], e["status"])
        lines.append(f"{e['engineer']}: {e.get('did', 'no activity')} [{status}]")
    return "\n".join(lines)


def _format_activity_for_voice(ctx: dict) -> str:
    github = ctx.get("github", {})
    if not github:
        return "GitHub data unavailable."
    commits = github.get("recent_commits", [])
    prs = github.get("open_prs", [])
    return f"{len(commits)} commits, {len(prs)} open PRs in last 24 hours"
```

---

## 6. LangGraph Orchestrator (Multi-Agent)

```python
# app/services/orchestrator.py
"""
LangGraph-based orchestrator.
Routes inputs to the correct workflow agent.
All agents output staged actions — nothing executes without human approval.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.services import (
    standup_agent,
    blocker_agent,
    sprint_agent,
    report_agent,
    backlog_agent,
)
from app.services.review_queue import stage_actions
import structlog

log = structlog.get_logger()

MAX_AGENT_ITERATIONS = 5  # hard limit on any agent loop


class PilotPMState(TypedDict):
    input: str
    input_type: str          # "email" | "slack" | "scheduled" | "manual"
    workflow: str            # classified workflow type
    context_snapshot: dict   # from ContextBuilder
    agent_steps: list        # log of reasoning steps (shown in UI)
    draft_actions: list      # actions awaiting human approval
    error: str | None
    status: str              # "running" | "awaiting_review" | "complete" | "error"


# ── Classification node ────────────────────────────────────────────────────────

async def classify_input(state: PilotPMState) -> PilotPMState:
    """Route the input to the correct workflow."""
    try:
        workflow = await call_ai(
            system=Prompts.CLASSIFIER_SYSTEM,
            user=Prompts.CLASSIFIER_USER.format(input=state["input"]),
            task="classify",
            temperature=0.0,
        )
        workflow = workflow.strip().lower()
        valid = {"standup", "blocker", "sprint", "report", "backlog", "voice", "unknown"}
        if workflow not in valid:
            workflow = "unknown"
        log.info("orchestrator.classified", input=state["input"][:50], workflow=workflow)
        return {**state, "workflow": workflow,
                "agent_steps": [f"Classified as: {workflow}"]}
    except Exception as e:
        return {**state, "workflow": "unknown", "error": str(e), "status": "error"}


# ── Router ─────────────────────────────────────────────────────────────────────

def route_workflow(state: PilotPMState) -> Literal[
    "standup", "blocker", "sprint", "report", "backlog", "unknown"
]:
    return state["workflow"]


# ── Human review gate ──────────────────────────────────────────────────────────

async def queue_for_review(state: PilotPMState) -> PilotPMState:
    """Stage all draft actions for PM approval. Nothing executes here."""
    if state["draft_actions"]:
        await stage_actions(state["draft_actions"])
        log.info("orchestrator.queued", action_count=len(state["draft_actions"]))
    return {**state, "status": "awaiting_review"}


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(PilotPMState)

    graph.add_node("classify", classify_input)
    graph.add_node("standup", standup_agent.run)
    graph.add_node("blocker", blocker_agent.run)
    graph.add_node("sprint", sprint_agent.run)
    graph.add_node("report", report_agent.run)
    graph.add_node("backlog", backlog_agent.run)
    graph.add_node("human_review", queue_for_review)
    graph.add_node("unknown", lambda s: {**s, "status": "error",
                                         "error": "Could not classify input"})

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", route_workflow)

    # All workflow agents → human review (no direct execution)
    for agent in ["standup", "blocker", "sprint", "report", "backlog"]:
        graph.add_edge(agent, "human_review")

    graph.add_edge("human_review", END)
    graph.add_edge("unknown", END)

    return graph.compile()


pilot_graph = build_graph()
```

---

## 7. Workflow Agents

```python
# app/services/standup_agent.py
"""F-001: Async Standup Digest"""

import json
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.services.context_builder import get_context_snapshot
from app.lib.retry import llm_retry
import structlog

log = structlog.get_logger()
MAX_ITERATIONS = 5  # hard limit (single-shot agent, but retry counts as iteration)


@llm_retry(max_retries=3)
async def _synthesize_digest(ctx: dict) -> dict:
    raw = await call_ai(
        system=Prompts.STANDUP_SYSTEM,
        user=Prompts.STANDUP_USER.format(
            timestamp=ctx["refreshed_at"],
            team_names=", ".join(ctx.get("github", {}).get("engineers", [])),
            github_data=json.dumps(ctx.get("github", {}), indent=2),
            slack_data=json.dumps(ctx.get("slack", {}), indent=2),
            monday_data=json.dumps(ctx.get("monday", {}), indent=2),
        ),
        task="general",
        temperature=0.3,
        max_tokens=3000,
    )
    return _parse_json_output(raw)


async def run(state: dict) -> dict:
    steps = state.get("agent_steps", [])
    draft_actions = []

    steps.append("Fetching project context snapshot...")
    ctx = await get_context_snapshot()

    gaps = [k for k, v in ctx["sources_available"].items() if not v]
    if gaps:
        steps.append(f"Warning: {', '.join(gaps)} unavailable — partial digest")

    steps.append("Synthesizing standup digest with primary LLM (Lava)")
    digest = await _synthesize_digest(ctx)

    if not digest:
        return {**state, "status": "error",
                "error": "Failed to parse digest after 3 retries",
                "agent_steps": steps}

    steps.append(f"Digest ready — {len(digest.get('digest', []))} engineers, "
                 f"status: {[e['status'] for e in digest.get('digest', [])]}")

    # Cache digest for voice agent consumption
    from app.db.mongo import get_collection
    col = get_collection("project_context")
    await col.update_one({}, {"$set": {"standup_cache": digest}})

    # Stage Slack post action for human approval
    draft_actions.append({
        "type": "slack_message",
        "title": "Post standup digest to Slack",
        "description": "Post today's AI standup digest to #standup-digest channel",
        "data": {
            "channel": "#standup-digest",
            "message": _format_digest_for_slack(digest),
        },
        "reasoning": steps.copy(),
    })

    return {**state, "agent_steps": steps, "draft_actions": draft_actions,
            "status": "awaiting_review", "result": digest}


def _format_digest_for_slack(digest: dict) -> str:
    lines = [f"*PilotPM Standup — {digest.get('generated_at', 'today')}*\n"]
    for eng in digest.get("digest", []):
        emoji = {"on_track": "🟢", "blocked": "🔴", "check_in": "🟡"}.get(eng["status"], "⚪")
        lines.append(f"{emoji} *{eng['engineer']}*: {eng.get('did', 'no activity')}")
        if eng.get("blocker"):
            lines.append(f"   🚫 Blocked: {eng['blocker']}")
    lines.append(f"\n_{digest.get('summary', '')}_")
    return "\n".join(lines)


def _parse_json_output(raw: str) -> dict | None:
    import re
    # Strip markdown code blocks if present
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip("` \n")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("standup.json_parse_failed", raw_preview=raw[:200])
        return None
```

```python
# app/services/sprint_agent.py
"""F-003: Sprint Autopilot (uses K2 Think V2)"""

import json
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.retry import llm_retry
from app.services.monday_service import MondayService
from app.services.github_service import GitHubService
import structlog

log = structlog.get_logger()
MAX_ITERATIONS = 5


@llm_retry(max_retries=2)
async def _score_sprint(backlog, velocity, carry_forward, sprint_number) -> dict:
    raw = await call_ai(
        system=Prompts.SPRINT_SYSTEM,
        user=Prompts.SPRINT_USER.format(
            sprint_number=sprint_number,
            sprint_days=14,
            velocity_data=json.dumps(velocity, indent=2),
            backlog_tickets=json.dumps(backlog, indent=2),
            carry_forward=json.dumps(carry_forward, indent=2),
        ),
        task="sprint",       # routes to K2 Think V2
        temperature=0.0,
        max_tokens=8192,
    )
    import re
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip("` \n")
    return json.loads(raw)


async def run(state: dict) -> dict:
    steps = state.get("agent_steps", [])
    draft_actions = []

    steps.append("Fetching backlog from Monday.com...")
    backlog = await MondayService.get_backlog()

    if len(backlog) < 3:
        steps.append(f"Warning: Only {len(backlog)} tickets in backlog — sprint may be under-capacity")

    steps.append("Calculating engineer velocity from GitHub (last 3 sprints)...")
    velocity = await GitHubService.get_velocity_per_engineer(sprints=3)

    steps.append("Fetching carry-forward tickets from current sprint...")
    carry_forward = await MondayService.get_incomplete_tickets()

    current_sprint_num = await MondayService.get_current_sprint_number()
    next_sprint = current_sprint_num + 1

    steps.append(f"K2 Think V2 scoring {len(backlog)} tickets for Sprint {next_sprint}...")
    sprint_plan = await _score_sprint(backlog, velocity, carry_forward, next_sprint)

    selected = [t for t in sprint_plan.get("tickets", []) if t.get("selected")]
    deferred = sprint_plan.get("deferred", [])
    utilization = sprint_plan.get("utilization_pct", 0)

    steps.append(f"Sprint {next_sprint} draft: {len(selected)} tickets, "
                 f"{utilization}% capacity, {len(deferred)} deferred")

    draft_actions.append({
        "type": "monday_sprint",
        "title": f"Create Sprint {next_sprint} in Monday.com",
        "description": f"{len(selected)} tickets, {utilization}% capacity",
        "data": {"sprint_plan": sprint_plan},
        "reasoning": steps.copy(),
    })

    draft_actions.append({
        "type": "calendar_events",
        "title": "Book sprint ceremonies in Calendar",
        "description": "Sprint planning, mid-sprint check, retro",
        "data": {"sprint_number": next_sprint, "duration_days": 14},
        "reasoning": [],
    })

    return {**state, "agent_steps": steps, "draft_actions": draft_actions,
            "status": "awaiting_review", "result": sprint_plan}
```

---

## 8. Context Window Budget

```python
# Context budgets — tune per provider defaults (gpt-4o / Gemini vary by model)
# K2 Think V2 context window: 128K tokens (check MBZUAI docs)

TOKEN_BUDGET_GENERAL = {
    "system_prompt":    2_000,   # fixed per agent
    "context_snapshot": 30_000,  # GitHub + Slack + Monday data (24hrs)
    "conversation":     5_000,   # multi-turn (review edits)
    "output_reserved":  4_096,   # max response
    # Total used: ~41K — stay within chosen model context limits
}

TOKEN_BUDGET_K2 = {
    "system_prompt":    2_000,
    "backlog_tickets":  20_000,  # 100 tickets × ~200 tokens each
    "velocity_data":    2_000,
    "output_reserved":  8_192,   # Sprint plans are long
    # Total used: ~32K / 128K available
}

TOKEN_BUDGET_VOICE = {
    "system_prompt":    1_500,   # ElevenLabs prompt (condensed context injected)
    "context_snapshot": 800,     # Voice needs brief context only
    # Total: ~2,300 — fits comfortably
}

MAX_HISTORY_TURNS = 5  # for any multi-turn agent interaction

def trim_history(messages: list[dict]) -> list[dict]:
    """Keep only the most recent turns to avoid context overflow."""
    if len(messages) <= MAX_HISTORY_TURNS * 2:
        return messages
    return messages[-(MAX_HISTORY_TURNS * 2):]
```

---

## 9. Guardrails

```python
# app/services/ai/guardrails.py
"""
Input and output guardrails for PilotPM.
Safety level: Medium (internal PM tool, no public-facing LLM input).
Primary risks: injection via GitHub commit messages or Slack messages.
"""

import re
import json
import structlog

log = structlog.get_logger()


class InputGuardrails:
    MAX_INPUT_CHARS = 50_000          # GitHub commit data can be large
    MAX_SINGLE_FIELD_CHARS = 10_000   # any single field (commit message, Slack msg)

    # Injection patterns that could appear in commit messages or Slack
    INJECTION_PATTERNS = [
        r"ignore (previous|all|above) instructions",
        r"you are now",
        r"new (system )?instructions?:",
        r"disregard (your|all|previous)",
        r"</?(system|prompt|instructions)>",
        r"act as (?!a PM|an? engineer|the)",  # allow "act as a PM" metaphors
    ]

    @classmethod
    def validate(cls, text: str) -> tuple[bool, str | None]:
        if len(text) > cls.MAX_INPUT_CHARS:
            # Truncate rather than reject — partial data is better than no data
            log.warning("guardrails.input_truncated", original_len=len(text))
            return True, None  # truncation handled upstream

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text.lower()):
                log.warning("guardrails.injection_detected", pattern=pattern,
                            text_preview=text[:100])
                return False, f"Disallowed pattern detected: {pattern}"

        return True, None

    @classmethod
    def sanitize_github_data(cls, data: dict) -> dict:
        """Truncate commit messages and PR descriptions to prevent injection."""
        if "commits" in data:
            for commit in data["commits"]:
                if "message" in commit:
                    commit["message"] = commit["message"][:500]  # truncate long messages
        return data

    @classmethod
    def sanitize_slack_data(cls, messages: list) -> list:
        """Truncate individual Slack messages."""
        sanitized = []
        for msg in messages:
            if isinstance(msg, dict) and "text" in msg:
                msg = {**msg, "text": msg["text"][:cls.MAX_SINGLE_FIELD_CHARS]}
            sanitized.append(msg)
        return sanitized


class OutputGuardrails:

    @staticmethod
    def parse_json_strict(output: str, required_keys: list[str]) -> dict | None:
        """Parse JSON output and validate required keys are present."""
        # Strip markdown code fences
        clean = re.sub(r"```(?:json)?\s*", "", output).strip("` \n")
        try:
            parsed = json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            log.warning("output_guardrails.json_parse_failed",
                        preview=output[:200])
            return None

        missing = [k for k in required_keys if k not in parsed]
        if missing:
            log.warning("output_guardrails.missing_keys", missing=missing)
            return None

        return parsed

    @staticmethod
    def validate_standup_output(output: dict) -> bool:
        """Verify standup digest has required structure."""
        if "digest" not in output:
            return False
        for eng in output["digest"]:
            if "engineer" not in eng or "status" not in eng:
                return False
            if eng["status"] not in {"on_track", "blocked", "check_in"}:
                return False
        return True

    @staticmethod
    def validate_sprint_output(output: dict) -> bool:
        """Verify sprint plan has required structure and reasonable capacity."""
        if "tickets" not in output or "utilization_pct" not in output:
            return False
        if output["utilization_pct"] > 120:  # sanity check
            log.warning("output_guardrails.sprint_over_capacity",
                        utilization=output["utilization_pct"])
            return False
        return True
```

---

## 10. Retry Decorator

```python
# app/lib/retry.py
"""
Retry decorator for all LLM calls.
Exponential backoff with jitter.
Applied via @llm_retry on every agent function that calls an LLM.
"""

import asyncio
import random
from functools import wraps
import structlog

log = structlog.get_logger()


def llm_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Retry decorator for async LLM calls.
    Uses exponential backoff with jitter to avoid thundering herd.

    Usage:
        @llm_retry(max_retries=3)
        async def call_something():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == max_retries - 1:
                        log.error("llm_retry.exhausted",
                                  func=func.__name__,
                                  attempts=max_retries,
                                  error=str(e))
                        raise

                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.5),
                                max_delay)
                    log.warning("llm_retry.retrying",
                                func=func.__name__,
                                attempt=attempt + 1,
                                delay=round(delay, 2),
                                error=str(e))
                    await asyncio.sleep(delay)

            raise last_error
        return wrapper
    return decorator


# Specific retry configs per use case
standup_retry = llm_retry(max_retries=3, base_delay=1.0)    # fast recovery
sprint_retry = llm_retry(max_retries=2, base_delay=2.0)     # K2 can be slow
voice_retry = llm_retry(max_retries=2, base_delay=0.5)      # voice needs speed
```

---

## 11. Failure Modes & Fallbacks

| Failure | Trigger | Fallback | User-Facing Message |
|---------|---------|---------|---------------------|
| Lava primary fails | HTTP 5XX or timeout | Second Lava call (`LAVA_MODEL_FALLBACK`) | Optional toast if UI surfaces model switch |
| Both Lava calls fail | Both error | Gemini direct if `GEMINI_API_KEY` set | Optional: "Using backup AI provider" |
| K2 Think V2 fails | timeout / 5XX | Continues to Lava chain (then optional Gemini) | Badge possible: "K2 unavailable — using backup" |
| Gemini fallback fails | 429 / 5XX | Surface last error (Lava) | Toast / error state |
| All AI unavailable | No provider succeeds | Serve cached data with staleness warning | Banner: "AI offline — showing cached data from [time]" |
| LLM returns invalid JSON | Parse fails | Retry with stricter JSON prompt (2× max) | No user-facing message (silent retry) |
| JSON still invalid after retry | 2 parse failures | Return partial result with `error` field | Warning banner on output card |
| GitHub API down | 4XX / 5XX | Partial context from Slack + Monday only | Yellow banner: "GitHub unavailable — partial digest" |
| Slack API down | 4XX / 5XX | Partial context from GitHub + Monday only | Yellow banner: "Slack unavailable — partial digest" |
| Monday.com MCP down | Timeout | Return cached sprint data (MongoDB) | Yellow banner: "Monday.com unavailable — using last known sprint" |
| Sprint over-capacity output | utilization > 120% | Guardrail triggers re-run with stricter capacity constraint | Silent retry (max 1) |
| Agent exceeds MAX_ITERATIONS | > 5 loops | Force stop, return partial result | Toast: "Agent couldn't complete — partial results shown" |
| Voice context stale | Cache > 2hrs old | Serve stale with spoken disclosure | Agent says: "My last update was [time] ago" |
| Lava forward unreachable | HTTP timeout | Retry (see `app/lib/retry.py`) + then Gemini if configured | Toast: "AI gateway unreachable — retrying..."

---

## 12. Cost Tracking

```python
# app/lib/cost.py
"""
Log token usage for observability (`app/lib/cost.py` logs `llm.cost`; dollar math optional).
Lava/K2/ElevenLabs pricing depends on your accounts — not hardcoded in production code.
"""

import structlog
log = structlog.get_logger()

PRICING = {
    "gpt-4o-mini":           {"input": 0.15,  "output": 0.60},   # example — verify OpenAI pricing
    "gpt-4o":                {"input": 2.50,  "output": 10.00}, # example
    "google/gemini-3-flash-preview": {"input": 0.00, "output": 0.00},  # set from Google billing
    "MBZUAI-IFM/K2-Think-v2": {"input": 0.00,  "output": 0.00},  # sponsor / event terms
    "elevenlabs-conv-ai":    {"input": 0.00,  "output": 0.00},   # free tier / your plan
}

HACKATHON_BUDGET_USD = 10.0  # hard cap — alert if exceeded
_session_cost_usd = 0.0


def log_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    p = PRICING.get(model, {"input": 0, "output": 0})
    cost = (input_tokens / 1_000_000) * p["input"] + \
           (output_tokens / 1_000_000) * p["output"]

    global _session_cost_usd
    _session_cost_usd += cost

    log.info("llm.cost",
             model=model,
             input_tokens=input_tokens,
             output_tokens=output_tokens,
             cost_usd=round(cost, 6),
             session_total_usd=round(_session_cost_usd, 4))

    if _session_cost_usd > HACKATHON_BUDGET_USD:
        log.error("cost.budget_exceeded",
                  session_total=_session_cost_usd,
                  budget=HACKATHON_BUDGET_USD)

    return cost


def get_session_cost() -> float:
    return round(_session_cost_usd, 4)
```

**Cost estimate for hackathon demo (rough):**

| Path | Calls (demo) | Notes |
|------|-------------|--------|
| Lava (gpt-4o-mini / gpt-4o) | most LLM calls | Metered via Lava + OpenAI upstream |
| K2 Think V2 | sprint/backlog | Per sponsor / event |
| Gemini direct | rare (Lava failures only) | Google AI billing if used |
| ElevenLabs voice | ~20 calls | Per ElevenLabs plan |

---

## 13. Eval Metrics

### Hackathon Demo Targets

| Metric | Target | Minimum Acceptable | How Measured |
|--------|--------|--------------------|--------------|
| Standup digest latency | < 30s | < 60s | Timer from trigger to rendered output |
| Standup accuracy | All 3 seeded engineers correct | 2/3 correct | Manual inspection of demo dataset |
| Blocker detection rate | 3/3 seeded blockers detected | 2/3 detected | Manual inspection |
| Blocker false positive rate | 0 false positives | ≤ 1 | Manual inspection |
| Sprint plan generation | < 90s for 20 tickets | < 120s | Timer from click to draft |
| Sprint capacity accuracy | ≤ 100% utilization | ≤ 105% | Check utilization_pct in output |
| Status report generation | < 15s | < 30s | Timer |
| Voice agent first response | < 3s from call connect | < 5s | Measured during test calls |
| Voice answer correctness | 3/3 demo questions correct | 2/3 correct | Live judge test |
| Lava → second model / optional Gemini | < 5s to detect + reroute | < 10s | Simulate Lava failure, measure recovery |

### Regression Test Dataset

```
test_data/
  standup_golden.jsonl      <- 3 engineers, seeded GitHub + Slack + Monday data
  blocker_golden.jsonl      <- 3 seeded blockers (PR stale, Slack signal, inactivity)
  sprint_golden.jsonl       <- 20 backlog tickets with expected top-5 ranking
  voice_qa.jsonl            <- 10 Q&A pairs (question + expected answer themes)
  adversarial_inputs.jsonl  <- injection attempts via commit messages
```

```python
# Run before demo to verify all agents working
# python -m pytest tests/agents/ -v --timeout=120
```

### Pre-Demo Checklist (run at 9am Sunday)

```
□ Lava forward smoke test passes (official `api.lava.so` + project test)
□ Lava forward reachable
□ GitHub API token valid (test: curl with token)
□ Slack bot can read + post (test: read #engineering, post to #test)
□ Monday.com MCP creates test board (verify + delete)
□ Gmail MCP sends test email (verify in inbox)
□ Twilio number receives test call
□ ElevenLabs voice agent answers and responds correctly
□ K2 Think V2 API returns response within 10s
□ Gemini last-resort works with `GEMINI_API_KEY` (break Lava creds, run standup — optional)
□ All 5 workflows run end-to-end on demo dataset
□ Review queue approves + executes a test action
□ No crashes in 3 consecutive full runs
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | March 28, 2026 | Aman | Initial — all 13 sections, PilotPM-specific |
| 1.1 | March 29, 2026 | — | Aligned LLM stack with code: Lava forward + OpenAI upstream, optional Gemini, K2 direct |
