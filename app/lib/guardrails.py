# app/lib/guardrails.py
"""Input/output validation for agent JSON."""

from __future__ import annotations

import re
import structlog

log = structlog.get_logger()

_VALID_STANDUP_STATUS = frozenset({"on_track", "blocked", "check_in"})


class InputGuardrails:
    MAX_INPUT_CHARS = 50_000
    MAX_SINGLE_FIELD_CHARS = 10_000

    INJECTION_PATTERNS = [
        r"ignore (previous|all|above) instructions",
        r"you are now",
        r"new (system )?instructions?:",
        r"disregard (your|all|previous)",
        r"</?(system|prompt|instructions)>",
        r"act as (?!a PM|an? engineer|the)",
    ]

    @classmethod
    def validate(cls, text: str) -> tuple[bool, str | None]:
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text.lower()):
                log.warning("guardrails.injection_detected", pattern=pattern, text_preview=text[:100])
                return False, f"Disallowed pattern detected: {pattern}"
        return True, None

    @classmethod
    def sanitize_github_data(cls, data: object) -> object:
        """Truncate PR/commit payloads to limit injection surface."""
        if isinstance(data, list):
            out = []
            for item in data[:500]:
                if isinstance(item, dict):
                    out.append(cls._truncate_github_item(item))
                else:
                    out.append(item)
            return out
        if isinstance(data, dict):
            if "commits" in data:
                for commit in data.get("commits", []):
                    if isinstance(commit, dict) and "message" in commit:
                        commit["message"] = str(commit["message"])[:500]
            return data
        return data

    @classmethod
    def _truncate_github_item(cls, item: dict) -> dict:
        m = dict(item)
        for k in ("title", "message", "text", "url"):
            if k in m and isinstance(m[k], str):
                m[k] = m[k][: cls.MAX_SINGLE_FIELD_CHARS]
        return m

    @classmethod
    def sanitize_slack_data(cls, messages: list) -> list:
        sanitized = []
        for msg in messages:
            if isinstance(msg, dict) and "text" in msg:
                msg = {**msg, "text": str(msg["text"])[: cls.MAX_SINGLE_FIELD_CHARS]}
            sanitized.append(msg)
        return sanitized


class OutputGuardrails:
    @staticmethod
    def validate_standup_output(data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("standup output must be a JSON object")
        if "digest" not in data:
            raise ValueError("standup digest missing 'digest' array")
        digest = data["digest"]
        if not isinstance(digest, list):
            raise ValueError("'digest' must be a list")
        for i, e in enumerate(digest):
            if not isinstance(e, dict):
                raise ValueError(f"digest[{i}] must be an object")
            for required in ("engineer", "status", "did", "working_on", "sources"):
                if required not in e:
                    raise ValueError(f"digest[{i}] missing '{required}'")
            if e["status"] not in _VALID_STANDUP_STATUS:
                raise ValueError(f"digest[{i}] invalid status: {e['status']}")
            if not isinstance(e.get("sources"), list):
                raise ValueError(f"digest[{i}] 'sources' must be a list")
        return data
