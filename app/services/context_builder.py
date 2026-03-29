# app/services/context_builder.py
"""
Builds and caches the project context snapshot.
Refreshed every 15 minutes via background task.
All agents consume this — no direct API calls from agents.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog

from app.db.mongo import get_collection
from app.integrations.github_service import GitHubService
from app.integrations.monday_service import MondayService
from app.integrations.slack_service import SlackService

log = structlog.get_logger()

CONTEXT_TTL_MINUTES = 15
CONTEXT_COLLECTION = "project_context"


def _parse_refreshed_at(raw: str) -> datetime:
    s = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


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
    await col.update_one({}, {"$set": snapshot}, upsert=True)
    log.info("context.refreshed", sources=snapshot["sources_available"])
    return snapshot


async def get_context_snapshot() -> dict:
    """Get cached context — refresh if stale."""
    col = get_collection(CONTEXT_COLLECTION)
    doc = await col.find_one({})

    if not doc:
        return await build_context_snapshot()

    refreshed_at = _parse_refreshed_at(doc["refreshed_at"])
    age_minutes = (datetime.now(UTC) - refreshed_at).total_seconds() / 60

    if age_minutes > CONTEXT_TTL_MINUTES:
        return await build_context_snapshot()

    return doc


async def get_context_for_voice() -> dict:
    """
    Voice agent needs a condensed context that fits the ElevenLabs system prompt.
    Returns human-readable strings, not raw API data.
    """
    ctx = await get_context_snapshot()
    snapshot = ctx.get("monday") or {}

    blockers_summary = _format_blockers_for_voice(ctx)
    standup_summary = _format_standup_for_voice(ctx)
    recent_activity = _format_activity_for_voice(ctx)

    return {
        "refresh_timestamp": ctx["refreshed_at"],
        "sprint_name": snapshot.get("sprint_name", "current sprint"),
        "days_remaining": snapshot.get("days_remaining", "unknown"),
        "velocity_pct": snapshot.get("velocity_pct", "unknown"),
        "blocker_count": len(ctx.get("blockers_cache") or []),
        "blockers_summary": blockers_summary,
        "standup_summary": standup_summary,
        "recent_activity": recent_activity,
    }


def _format_blockers_for_voice(ctx: dict) -> str:
    blockers = ctx.get("blockers_cache") or []
    if not blockers:
        return "No active blockers."
    lines = []
    for b in blockers[:3]:
        lines.append(f"{b['engineer']} — {b['description']} ({b['blocked_for']})")
    return "\n".join(lines)


def _format_standup_for_voice(ctx: dict) -> str:
    digest = (ctx.get("standup_cache") or {}).get("digest", [])
    if not digest:
        return "No standup data available."
    lines = []
    for e in digest:
        status_map = {"blocked": "BLOCKED", "check_in": "CHECK IN", "on_track": "on track"}
        status = status_map.get(e["status"], e["status"])
        lines.append(f"{e['engineer']}: {e.get('did', 'no activity')} [{status}]")
    return "\n".join(lines)


def _format_activity_for_voice(ctx: dict) -> str:
    github = ctx.get("github") or {}
    if not github:
        return "GitHub data unavailable."
    commits = github.get("commits") or {}
    prs = github.get("pull_requests") or {}
    n_commits = sum(len(v) for v in commits.values() if isinstance(v, list))
    n_prs = sum(len(v) for v in prs.values() if isinstance(v, list))
    return f"{n_commits} commits, {n_prs} open PRs in last 24 hours"
