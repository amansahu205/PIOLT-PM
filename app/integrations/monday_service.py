# app/integrations/monday_service.py
"""
Monday.com GraphQL API with demo_monday MongoDB fallback.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
import structlog

from app.config import settings
from app.db.mongo import get_collection

log = structlog.get_logger()

MONDAY_API = "https://api.monday.com/v2"
DEMO_COLLECTION = "demo_monday"

MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID", "").strip()


class MondayService:
    """Monday.com GraphQL client; falls back to seeded `demo_monday` documents."""

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "Authorization": settings.MONDAY_API_KEY,
            "Content-Type": "application/json",
            "API-Version": "2024-10",
        }

    @staticmethod
    async def _graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                MONDAY_API,
                headers=MondayService._headers(),
                json={"query": query, "variables": variables or {}},
            )
            r.raise_for_status()
            body = r.json()
        if body.get("errors"):
            raise RuntimeError(str(body["errors"]))
        return body.get("data") or {}

    @staticmethod
    async def _load_demo_docs() -> list[dict[str, Any]]:
        col = get_collection(DEMO_COLLECTION)
        return await col.find({}).to_list(length=500)

    # ── Fallback (seed: sprint_snapshot + ticket) ────────────────────────────

    @staticmethod
    def _fallback_sprint_status(docs: list[dict[str, Any]]) -> dict[str, Any]:
        snap = next((d for d in docs if d.get("doc_type") == "sprint_snapshot"), None)
        tickets = [d for d in docs if d.get("doc_type") == "ticket"]
        if not snap:
            return {"sprint_name": "unknown", "tickets": [], "velocity_pct": 0}
        total = int(snap.get("total_tickets") or 0)
        done = len([t for t in tickets if t.get("status") == "done"])
        velocity_pct = int(round((done / total) * 100)) if total else 0
        return {
            "sprint_name": snap.get("sprint_name"),
            "tickets": tickets,
            "velocity_pct": velocity_pct,
            "board_id": snap.get("board_id"),
            "in_progress_count": snap.get("in_progress_count"),
            "updated_at": snap.get("updated_at"),
        }

    @staticmethod
    def _fallback_backlog(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            t
            for t in docs
            if t.get("doc_type") == "ticket"
            and (t.get("sprint") in (None, "", "Backlog") or t.get("in_backlog") is True)
        ]

    @staticmethod
    def _fallback_incomplete(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            t
            for t in docs
            if t.get("doc_type") == "ticket" and t.get("status") == "in_progress"
        ]

    @staticmethod
    def _fallback_sprint_number(docs: list[dict[str, Any]]) -> int:
        snap = next((d for d in docs if d.get("doc_type") == "sprint_snapshot"), None)
        name = (snap or {}).get("sprint_name") or ""
        m = re.search(r"(\d+)", name)
        return int(m.group(1)) if m else 1

    @staticmethod
    def _fallback_stale_in_progress(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for t in docs:
            if t.get("doc_type") != "ticket" or t.get("status") != "in_progress":
                continue
            days = t.get("days_in_status")
            if days is None:
                days = 5.0
            if float(days) > 3:
                row = dict(t)
                row["days_in_status"] = float(days)
                out.append(row)
        return out

    # ── Public API ───────────────────────────────────────────────────────────

    @staticmethod
    async def get_sprint_status() -> dict[str, Any]:
        if not MONDAY_BOARD_ID:
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_sprint_status(docs)
        try:
            q = """
            query ($ids: [ID!]) {
              boards(ids: $ids) {
                id
                name
                items_page(limit: 100) {
                  items {
                    id
                    name
                    state
                  }
                }
              }
            }
            """
            data = await MondayService._graphql(q, {"ids": [MONDAY_BOARD_ID]})
            boards = data.get("boards") or []
            if not boards:
                raise RuntimeError("no_boards")
            b = boards[0]
            items = ((b.get("items_page") or {}).get("items")) or []
            done = len([i for i in items if (i.get("state") or "").lower() == "done"])
            velocity_pct = min(100, int(round((done / max(len(items), 1)) * 100)))
            return {
                "sprint_name": b.get("name"),
                "tickets": items,
                "velocity_pct": velocity_pct,
                "board_id": b.get("id"),
            }
        except Exception as e:
            log.warning("monday.get_sprint_status.fallback", error=str(e))
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_sprint_status(docs)

    @staticmethod
    async def get_backlog() -> list[dict[str, Any]]:
        if not MONDAY_BOARD_ID:
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_backlog(docs)
        try:
            q = """
            query ($ids: [ID!]) {
              boards(ids: $ids) {
                items_page(limit: 200) {
                  items {
                    id
                    name
                    state
                  }
                }
              }
            }
            """
            data = await MondayService._graphql(q, {"ids": [MONDAY_BOARD_ID]})
            boards = data.get("boards") or []
            items = ((boards[0].get("items_page") or {}).get("items")) if boards else []
            # Heuristic: items not in an active sprint are not in API payload — return items in "backlog" state
            return [
                i
                for i in (items or [])
                if (i.get("state") or "").lower() in ("backlog", "pending", "open")
            ]
        except Exception as e:
            log.warning("monday.get_backlog.fallback", error=str(e))
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_backlog(docs)

    @staticmethod
    async def get_incomplete_tickets() -> list[dict[str, Any]]:
        if not MONDAY_BOARD_ID:
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_incomplete(docs)
        try:
            q = """
            query ($ids: [ID!]) {
              boards(ids: $ids) {
                items_page(limit: 200) {
                  items {
                    id
                    name
                    state
                  }
                }
              }
            }
            """
            data = await MondayService._graphql(q, {"ids": [MONDAY_BOARD_ID]})
            boards = data.get("boards") or []
            items = ((boards[0].get("items_page") or {}).get("items")) if boards else []
            return [
                i
                for i in (items or [])
                if (i.get("state") or "").lower() in ("active", "working", "in_progress", "started")
            ]
        except Exception as e:
            log.warning("monday.get_incomplete_tickets.fallback", error=str(e))
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_incomplete(docs)

    @staticmethod
    async def get_current_sprint_number() -> int:
        try:
            st = await MondayService.get_sprint_status()
            name = str(st.get("sprint_name") or "")
            m = re.search(r"(\d+)", name)
            return int(m.group(1)) if m else 1
        except Exception as e:
            log.warning("monday.get_current_sprint_number.fallback", error=str(e))
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_sprint_number(docs)

    @staticmethod
    async def get_stale_in_progress_tickets() -> list[dict[str, Any]]:
        if not MONDAY_BOARD_ID:
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_stale_in_progress(docs)
        try:
            # Without per-item time columns, fall back to demo heuristic
            raise RuntimeError("stale_requires_demo_or_columns")
        except Exception as e:
            log.warning("monday.get_stale_in_progress.fallback", error=str(e))
            docs = await MondayService._load_demo_docs()
            return MondayService._fallback_stale_in_progress(docs)

    @staticmethod
    async def create_board(name: str, tasks: list[Any]) -> str:
        _ = tasks
        try:
            mut = """
            mutation ($name: String!, $kind: BoardKind!) {
              create_board(board_name: $name, board_kind: $kind) {
                id
              }
            }
            """
            data = await MondayService._graphql(mut, {"name": name, "kind": "public"})
            cb = data.get("create_board") or {}
            bid = cb.get("id")
            if bid:
                return str(bid)
            raise RuntimeError("create_board_missing_id")
        except Exception as e:
            log.warning("monday.create_board.fallback", error=str(e))
            return "board_demo_001"

    @staticmethod
    async def update_task_status(task_id: str, status: str) -> bool:
        if not MONDAY_BOARD_ID:
            return False
        try:
            mut = """
            mutation ($board_id: ID!, $item_id: ID!, $column_id: String!, $value: JSON!) {
              change_column_value(
                board_id: $board_id
                item_id: $item_id
                column_id: $column_id
                value: $value
              ) {
                id
              }
            }
            """
            value = json.dumps({"label": status})
            await MondayService._graphql(
                mut,
                {
                    "board_id": str(MONDAY_BOARD_ID),
                    "item_id": str(task_id),
                    "column_id": "status",
                    "value": value,
                },
            )
            return True
        except Exception as e:
            log.warning("monday.update_task_status.failed", error=str(e))
            return False
