# app/services/blocker_service.py
"""Blocker Radar — F-002: detect blockers from PRs, Slack, tickets."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.integrations.github_service import GitHubService
from app.integrations.monday_service import MondayService
from app.integrations.slack_service import SlackService
from app.lib.guardrails import InputGuardrails
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.retry import llm_retry
from app.models.blocker import BlockerCard
from app.repositories.blocker_repo import BlockerRepository
from app.services import review_service

log = structlog.get_logger()


def _parse_blocker_json(raw: str) -> dict | None:
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
    raw = raw.strip("` \n")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("blocker_scan.json_parse_failed", raw_preview=raw[:200])
        return None


def _dedupe_key(card: BlockerCard) -> str:
    return f"{card.engineer}|{card.type}|{card.description[:120]}"


@llm_retry(max_retries=2)
async def _run_blocker_scan_inner(db: AsyncIOMotorDatabase) -> list[BlockerCard]:
    pr_data, slack_data, ticket_data, commit_activity = await asyncio.gather(
        GitHubService.get_open_prs_with_age(),
        SlackService.get_recent_messages(hours=48),
        MondayService.get_stale_in_progress_tickets(),
        GitHubService.get_commit_activity_per_engineer(),
        return_exceptions=True,
    )

    def _exc_or_val(x: object, name: str) -> object:
        if isinstance(x, BaseException):
            log.warning("blocker_scan.source_failed", source=name, error=str(x))
            return [] if name != "commits" else {}
        return x

    pr_data = _exc_or_val(pr_data, "prs")
    slack_data = _exc_or_val(slack_data, "slack")
    ticket_data = _exc_or_val(ticket_data, "tickets")
    commit_activity = _exc_or_val(commit_activity, "commits")

    pr_data = InputGuardrails.sanitize_github_data(pr_data)
    slack_list = slack_data if isinstance(slack_data, list) else []
    slack_data = InputGuardrails.sanitize_slack_data(slack_list)

    team_names = ["Sarah", "Mike", "Alex", "Jordan"]
    commit_json = json.dumps(commit_activity, indent=2)[:4000] if commit_activity else "{}"
    ticket_json = json.dumps(ticket_data, indent=2)[:4000] if ticket_data else "[]"

    user_prompt = Prompts.BLOCKER_USER.format(
        timestamp=datetime.now(UTC).isoformat(),
        team_names=", ".join(team_names),
        pr_data=json.dumps(pr_data, indent=2)[:8000],
        slack_data=json.dumps(slack_data, indent=2)[:8000],
        commit_activity=commit_json,
        ticket_activity=ticket_json,
    )

    if len(user_prompt) > InputGuardrails.MAX_INPUT_CHARS:
        user_prompt = user_prompt[: InputGuardrails.MAX_INPUT_CHARS]
        log.warning("blocker_scan.prompt_truncated", max_len=InputGuardrails.MAX_INPUT_CHARS)

    ok, err = InputGuardrails.validate(user_prompt)
    if not ok:
        log.error("blocker_scan.guardrails_rejected", error=err)
        return await BlockerRepository.find_active(db)

    response = await call_ai(
        system=Prompts.BLOCKER_SYSTEM,
        user=user_prompt,
        task="general",
        temperature=0.1,
        max_tokens=2000,
    )

    parsed = _parse_blocker_json(response)
    if not parsed:
        return await BlockerRepository.find_active(db)

    blockers_raw = parsed.get("blockers", [])
    if not isinstance(blockers_raw, list):
        blockers_raw = []

    existing = await BlockerRepository.find_active(db)
    existing_keys = {_dedupe_key(c) for c in existing}

    now = datetime.now(UTC)
    for b in blockers_raw:
        if not isinstance(b, dict):
            continue
        b = dict(b)
        b.pop("id", None)
        try:
            card = BlockerCard.model_validate(
                {
                    **b,
                    "status": "active",
                    "detected_at": now,
                    "updated_at": now,
                }
            )
        except Exception as e:
            log.warning("blocker_scan.card_skip", error=str(e))
            continue

        key = _dedupe_key(card)
        if key in existing_keys:
            continue

        inserted = await BlockerRepository.insert(card, db)
        existing_keys.add(key)

        await review_service.stage_action(
            action_type="slack_ping",
            title="Slack ping for blocker",
            description="Draft message to unblock work (review before sending)",
            data={
                "channel": settings.SLACK_ENGINEERING_CHANNEL,
                "text": card.draft_ping or f"Blocker: {card.description}",
                "blocker_id": inserted.id,
            },
            reasoning=f"New blocker detected: {card.severity} — {card.type}",
            workflow="blocker",
            db=db,
        )

    return await BlockerRepository.find_active(db)


class BlockerService:
    @staticmethod
    async def get_active_blockers(db: AsyncIOMotorDatabase) -> list[BlockerCard]:
        return await BlockerRepository.find_active(db)

    @staticmethod
    async def get_resolved(days: int, db: AsyncIOMotorDatabase) -> list[BlockerCard]:
        return await BlockerRepository.find_resolved(days=days, db=db)

    @staticmethod
    async def dismiss(
        blocker_id: str,
        reason: str,
        db: AsyncIOMotorDatabase,
    ) -> BlockerCard | None:
        updated = await BlockerRepository.update_status(
            blocker_id, "dismissed", reason or None, db
        )
        if not updated:
            return None
        log.info("blocker.dismissed", id=blocker_id, reason=reason)
        return updated

    @staticmethod
    async def run_blocker_scan(db: AsyncIOMotorDatabase) -> list[BlockerCard]:
        return await _run_blocker_scan_inner(db)
