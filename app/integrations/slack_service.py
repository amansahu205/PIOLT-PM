# app/integrations/slack_service.py
"""
Slack Web API integration with demo_slack MongoDB fallback for reads.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog

from app.config import settings
from app.db.mongo import get_collection

log = structlog.get_logger()

SLACK_API = "https://slack.com/api"
DEMO_COLLECTION = "demo_slack"

_slack_lock = asyncio.Lock()
_last_slack_monotonic = 0.0


async def _rate_limit_before_request() -> None:
    """At most one Slack API call per second (gap >= 1s between calls)."""
    global _last_slack_monotonic
    async with _slack_lock:
        now = time.monotonic()
        elapsed = now - _last_slack_monotonic
        if _last_slack_monotonic > 0.0 and elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _last_slack_monotonic = time.monotonic()


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        s = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _normalize_channel_name(channel: str) -> str:
    c = channel.strip()
    return c if c.startswith("#") else f"#{c}"


class SlackService:
    """Slack Web API helper; `get_recent_messages` falls back to `demo_slack`."""

    @staticmethod
    async def _load_demo_messages() -> list[dict[str, Any]]:
        col = get_collection(DEMO_COLLECTION)
        return await col.find({}).to_list(length=2000)

    @staticmethod
    async def _api_post_json(client: httpx.AsyncClient, path: str, body: dict[str, Any]) -> dict[str, Any]:
        await _rate_limit_before_request()
        url = f"{SLACK_API}/{path.lstrip('/')}"
        r = await client.post(url, headers=_auth_headers(), json=body)
        r.raise_for_status()
        return r.json()

    @staticmethod
    async def _api_get(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
        await _rate_limit_before_request()
        url = f"{SLACK_API}/{path.lstrip('/')}"
        r = await client.get(url, headers=_auth_headers(), params=params)
        r.raise_for_status()
        return r.json()

    @staticmethod
    async def _resolve_channel_id(client: httpx.AsyncClient, channel: str) -> str | None:
        """Resolve #name or C… id to a channel ID."""
        ch = channel.strip()
        if ch.startswith("C") and len(ch) > 5:
            return ch
        name = ch.lstrip("#").lower()
        data = await SlackService._api_get(
            client,
            "conversations.list",
            {"types": "public_channel,private_channel", "limit": 1000},
        )
        if not data.get("ok"):
            log.warning("slack.conversations.list_failed", error=data.get("error"))
            return None
        for c in data.get("channels", []):
            if c.get("name", "").lower() == name:
                return c.get("id")
        return None

    @staticmethod
    async def get_recent_messages(hours: int = 48, channel: str | None = None) -> list[dict[str, Any]]:
        """
        Recent channel messages. Uses conversations.history when the API works;
        otherwise returns matching rows from `demo_slack`.

        If `channel` is None, uses `settings.SLACK_ENGINEERING_CHANNEL` (env).
        """
        ch = (channel or settings.SLACK_ENGINEERING_CHANNEL or "#engineering").strip()
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        want = _normalize_channel_name(ch)

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                cid = await SlackService._resolve_channel_id(client, ch)
                if not cid:
                    raise RuntimeError("slack_channel_not_found")

                oldest = str(cutoff.timestamp())
                out: list[dict[str, Any]] = []
                cursor: str | None = None
                for _ in range(15):
                    params: dict[str, Any] = {
                        "channel": cid,
                        "limit": 200,
                        "oldest": oldest,
                    }
                    if cursor:
                        params["cursor"] = cursor
                    await _rate_limit_before_request()
                    url = f"{SLACK_API}/conversations.history"
                    r = await client.get(url, headers=_auth_headers(), params=params)
                    r.raise_for_status()
                    data = r.json()
                    if not data.get("ok"):
                        raise RuntimeError(data.get("error", "slack_api_error"))
                    for m in data.get("messages", []):
                        out.append(m)
                    cursor = (data.get("response_metadata") or {}).get("next_cursor") or None
                    if not cursor:
                        break
                return out
        except Exception as e:
            log.warning("slack.get_recent_messages.fallback", error=str(e))
            docs = await SlackService._load_demo_messages()
            result: list[dict[str, Any]] = []
            for d in docs:
                if _normalize_channel_name(d.get("channel", "")) != want:
                    continue
                ts = _parse_ts(d.get("ts"))
                if ts is None or ts < cutoff:
                    continue
                result.append(
                    {
                        "channel": d.get("channel"),
                        "user": d.get("user"),
                        "text": d.get("text"),
                        "ts": d.get("ts"),
                    }
                )
            return result

    @staticmethod
    async def post_message(channel: str, text: str) -> bool:
        """Post a message to a channel (#name or id). Returns True on ok."""
        body = {"channel": channel, "text": text}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                data = await SlackService._api_post_json(client, "chat.postMessage", body)
            if data.get("ok"):
                return True
            log.warning("slack.post_message.failed", error=data.get("error"))
            return False
        except Exception as e:
            log.warning("slack.post_message.exception", error=str(e))
            return False

    @staticmethod
    async def _resolve_user_id(client: httpx.AsyncClient, user_handle: str) -> str | None:
        handle = user_handle.strip().lstrip("@")
        data = await SlackService._api_get(
            client,
            "users.lookupByUsername",
            {"username": handle},
        )
        if data.get("ok") and data.get("user"):
            return (data["user"] or {}).get("id")
        log.warning("slack.users.lookupByUsername_failed", error=data.get("error"), handle=handle)
        return None

    @staticmethod
    async def send_dm(user_handle: str, text: str) -> bool:
        """Open a DM and post text. Uses users.lookupByUsername + conversations.open + chat.postMessage."""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                uid = await SlackService._resolve_user_id(client, user_handle)
                if not uid:
                    return False
                open_body = {"users": uid}
                open_data = await SlackService._api_post_json(client, "conversations.open", open_body)
                if not open_data.get("ok"):
                    log.warning("slack.conversations.open_failed", error=open_data.get("error"))
                    return False
                ch = (open_data.get("channel") or {}).get("id")
                if not ch:
                    return False
                pm = await SlackService._api_post_json(
                    client,
                    "chat.postMessage",
                    {"channel": ch, "text": text},
                )
                return bool(pm.get("ok"))
        except Exception as e:
            log.warning("slack.send_dm.exception", error=str(e))
            return False
