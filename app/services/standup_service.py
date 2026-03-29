# app/services/standup_service.py
"""F-001: Async standup digest."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.db.mongo import get_collection
from app.integrations.github_service import GitHubService
from app.lib.guardrails import OutputGuardrails
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.retry import llm_retry
from app.repositories.standup_repo import StandupRepository
from app.services import context_builder
from app.services import review_service

log = structlog.get_logger()


def _parse_json_output(raw: str) -> dict | None:
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    raw = raw.strip("` \n")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("standup.json_parse_failed", raw_preview=raw[:200])
        return None


@llm_retry(max_retries=3)
async def _llm_standup(user_prompt: str) -> str:
    return await call_ai(
        system=Prompts.STANDUP_SYSTEM,
        user=user_prompt,
        task="general",
        temperature=0.3,
        max_tokens=3000,
    )


class StandupService:
    @staticmethod
    async def generate_digest(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        ctx = await context_builder.get_context_snapshot()

        team_list = await GitHubService.get_team_members()
        team_names = ", ".join(team_list) if team_list else "Engineering"

        user_prompt = Prompts.STANDUP_USER.format(
            timestamp=ctx.get("refreshed_at", ""),
            team_names=team_names,
            github_data=json.dumps(ctx.get("github"), indent=2, default=str),
            slack_data=json.dumps(ctx.get("slack"), indent=2, default=str),
            monday_data=json.dumps(ctx.get("monday"), indent=2, default=str),
        )

        raw = await _llm_standup(user_prompt)
        digest = _parse_json_output(raw)
        if not digest:
            raise ValueError("Failed to parse standup JSON from model output")

        digest = OutputGuardrails.validate_standup_output(digest)
        digest["generated_at"] = digest.get("generated_at") or datetime.now(UTC).isoformat()

        col = get_collection(context_builder.CONTEXT_COLLECTION)
        await col.update_one({}, {"$set": {"standup_cache": digest}}, upsert=True)

        stored = await StandupRepository.insert(digest, db)

        await review_service.stage_action(
            action_type="slack_message",
            title="Post standup digest to Slack",
            description=f"Post today's AI standup digest to {settings.SLACK_STANDUP_CHANNEL}",
            data={
                "channel": settings.SLACK_STANDUP_CHANNEL,
                "message": review_service.format_digest_for_slack(digest),
            },
            reasoning="Standup digest generated from GitHub, Slack, and Monday.com context.",
            workflow="standup",
            db=db,
        )

        log.info(
            "standup.digest_generated",
            engineers=len(digest.get("digest", [])),
            sources=ctx.get("sources_available"),
        )
        return {**digest, "_id": stored.get("_id", "")}

    @staticmethod
    async def get_today_digest(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        doc = await StandupRepository.find_today(db)
        if doc:
            doc = dict(doc)
            if "_id" in doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        return await StandupService.generate_digest(db)

    @staticmethod
    async def get_history(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
        rows = await StandupRepository.find_recent(db, n=7)
        out: list[dict[str, Any]] = []
        for d in rows:
            d = dict(d)
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
            out.append(d)
        return out
