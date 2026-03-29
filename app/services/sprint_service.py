# app/services/sprint_service.py
"""F-003 Sprint Autopilot — planning, draft edits, approval staging."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.integrations.github_service import GitHubService
from app.integrations.monday_service import MondayService
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.retry import llm_retry
from app.models.sprint import SprintTicket
from app.repositories.sprint_repo import SprintRepository
from app.services import review_service

log = structlog.get_logger()

SPRINT_DAYS_DEFAULT = 14
AGENT_MODEL = settings.K2_MODEL


def _parse_sprint_json(raw: str) -> dict[str, Any] | None:
    text = re.sub(r"```(?:json)?\s*", "", raw).strip()
    text = text.strip("` \n")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("sprint.json_parse_failed", raw_preview=raw[:200])
        return None


def _team_capacity(velocity: dict[str, float]) -> float:
    return float(sum(velocity.values())) if velocity else 40.0


def _recalculate_utilization(plan: dict[str, Any]) -> dict[str, Any]:
    tickets = plan.get("tickets") or []
    total = float(plan.get("total_capacity_pts") or 0)
    if total <= 0:
        total = _team_capacity({})
    used = sum(
        float(t.get("estimated_pts", 0))
        for t in tickets
        if isinstance(t, dict) and t.get("selected", True)
    )
    util = (used / total * 100.0) if total > 0 else 0.0
    plan["total_capacity_pts"] = total
    plan["used_capacity_pts"] = round(used, 2)
    plan["utilization_pct"] = round(min(util, 999.0), 1)
    return plan


@llm_retry(max_retries=2)
async def _call_sprint_llm(user_prompt: str) -> str:
    return await call_ai(
        system=Prompts.SPRINT_SYSTEM,
        user=user_prompt,
        task="sprint",
        temperature=0.0,
        max_tokens=8192,
    )


class SprintService:
    @staticmethod
    async def get_current_sprint(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        raw = await MondayService.get_sprint_status()
        return {
            "sprint_name": raw.get("sprint_name"),
            "velocity_pct": int(raw.get("velocity_pct") or 0),
            "board_id": raw.get("board_id"),
            "tickets": raw.get("tickets") or [],
            "in_progress_count": raw.get("in_progress_count"),
            "updated_at": raw.get("updated_at"),
        }

    @staticmethod
    async def get_draft(db: AsyncIOMotorDatabase) -> dict[str, Any] | None:
        doc = await SprintRepository.find_draft(db)
        return SprintRepository._with_id(doc) if doc else None

    @staticmethod
    async def generate_draft(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        backlog, velocity, carry_forward = await asyncio_gather_sources()

        existing = await SprintRepository.find_draft(db)
        if existing and existing.get("sprint_number") is not None:
            sprint_number = int(existing["sprint_number"])
        else:
            sprint_number = await SprintRepository.get_sprint_number(db)

        team_cap = _team_capacity(velocity)
        user_prompt = Prompts.SPRINT_USER.format(
            sprint_number=sprint_number,
            sprint_days=SPRINT_DAYS_DEFAULT,
            velocity_data=json.dumps(velocity, indent=2),
            backlog_tickets=json.dumps(backlog, indent=2, default=str),
            carry_forward=json.dumps(carry_forward, indent=2, default=str),
        )

        raw = await _call_sprint_llm(user_prompt)
        parsed = _parse_sprint_json(raw)
        if not parsed:
            raise ValueError("Failed to parse sprint plan JSON from model output")

        parsed.setdefault("sprint_name", f"Sprint {sprint_number}")
        parsed.setdefault("tickets", [])
        parsed.setdefault("deferred", [])
        parsed["sprint_number"] = sprint_number
        parsed["status"] = "draft"
        parsed["agent_model"] = AGENT_MODEL

        if float(parsed.get("total_capacity_pts") or 0) <= 0:
            parsed["total_capacity_pts"] = team_cap

        _recalculate_utilization(parsed)

        util = float(parsed.get("utilization_pct") or 0)
        if util > 100.0:
            raise ValueError(
                f"Draft utilization is {util:.1f}% which exceeds 100%. "
                "Regenerate or reduce scope before saving."
            )

        await SprintRepository.delete_drafts(db)
        saved = await SprintRepository.insert(parsed, db)
        log.info(
            "sprint.draft_generated",
            sprint_number=sprint_number,
            utilization=parsed.get("utilization_pct"),
            model=AGENT_MODEL,
        )
        return saved

    @staticmethod
    async def update_draft_tickets(
        tickets: list[SprintTicket],
        db: AsyncIOMotorDatabase,
    ) -> dict[str, Any]:
        draft = await SprintRepository.find_draft(db)
        if not draft:
            raise ValueError("No sprint draft found — generate a draft first")

        plan_id = str(draft.get("_id") or draft.get("id") or "")
        data = dict(draft)
        data.pop("_id", None)
        data.pop("id", None)
        data["tickets"] = [t.model_dump() for t in tickets]
        data["status"] = "draft"
        _recalculate_utilization(data)

        updated = await SprintRepository.update(plan_id, data, db)
        if not updated:
            raise ValueError("Failed to update sprint draft")
        return updated

    @staticmethod
    async def approve_sprint(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        draft = await SprintRepository.find_draft(db)
        if not draft:
            raise ValueError("No sprint draft to approve")

        plan_id = str(draft.get("_id") or "")
        if not plan_id:
            raise ValueError("Invalid draft document (missing id)")

        plan = dict(draft)
        plan.pop("_id", None)
        util = float(plan.get("utilization_pct") or 0)
        if util > 110.0:
            raise ValueError(
                f"Sprint utilization is {util:.1f}% — cannot approve above 110%. "
                "Remove tickets or adjust estimates in the draft."
            )

        monday = await review_service.stage_action(
            action_type="monday_sprint",
            title="Apply sprint to Monday.com",
            description="Create/update sprint items and assignments on the engineering board",
            data={
                "sprint_plan_id": plan_id,
                "sprint_name": plan.get("sprint_name"),
                "sprint_number": plan.get("sprint_number"),
                "tickets": plan.get("tickets") or [],
            },
            reasoning=[
                "Sprint plan approved by PM.",
                f"Planned with {AGENT_MODEL} (K2 Think V2) reasoning for scoring and assignments.",
            ],
            workflow="sprint",
            db=db,
        )

        start_hint = datetime.now(UTC).date().isoformat()
        cal = await review_service.stage_action(
            action_type="calendar_events",
            title="Schedule sprint ceremonies",
            description="Add sprint planning, mid-sprint check-in, and review to team calendar",
            data={
                "sprint_plan_id": plan_id,
                "sprint_name": plan.get("sprint_name"),
                "duration_days": SPRINT_DAYS_DEFAULT,
                "suggested_start": start_hint,
                "events": [
                    {"title": "Sprint planning", "length_min": 60},
                    {"title": "Mid-sprint sync", "length_min": 30},
                    {"title": "Sprint review", "length_min": 45},
                ],
            },
            reasoning=[
                "Standard cadence for a 2-week sprint.",
                f"Aligned to draft {plan.get('sprint_name')!r} produced by {AGENT_MODEL}.",
            ],
            workflow="sprint",
            db=db,
        )

        staged = [monday, cal]
        log.info("sprint.approved", plan_id=plan_id, staged=len(staged))
        return {
            "message": "Sprint approved; review queue actions staged for Monday.com and calendar.",
            "staged_actions": staged,
            "agent_model": AGENT_MODEL,
        }


async def asyncio_gather_sources() -> tuple[list[dict], dict[str, float], list[dict]]:
    backlog, velocity, carry_forward = await asyncio.gather(
        MondayService.get_backlog(),
        GitHubService.get_velocity_per_engineer(sprints=3),
        MondayService.get_incomplete_tickets(),
        return_exceptions=True,
    )

    def _ok(val: object, default: Any, name: str) -> Any:
        if isinstance(val, BaseException):
            log.warning("sprint.source_failed", source=name, error=str(val))
            return default
        return val

    backlog = _ok(backlog, [], "backlog")
    velocity = _ok(velocity, {}, "velocity")
    carry_forward = _ok(carry_forward, [], "carry_forward")
    return backlog, velocity, carry_forward
