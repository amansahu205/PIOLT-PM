#!/usr/bin/env python3
"""
Smoke-test PilotPM API workflows via FastAPI TestClient (no separate server).

Run from repository root:
    uv run python scripts/test_workflows.py

Optional — also hit LLM-heavy endpoints (slow, uses credits):
    uv run python scripts/test_workflows.py --slow
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

load_dotenv(ROOT / ".env")

from app.main import app  # noqa: E402


def _hdr(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Run standup/blocker scan/sprint generate (calls external APIs + LLMs)",
    )
    args = parser.parse_args()

    email = os.environ.get("DEMO_EMAIL", "")
    password = os.environ.get("DEMO_PASSWORD", "")
    if not email or not password:
        print("Missing DEMO_EMAIL / DEMO_PASSWORD in environment.", file=sys.stderr)
        sys.exit(1)

    results: list[tuple[str, int, str]] = []

    with TestClient(app, raise_server_exceptions=False) as client:
        # --- Public ---
        r = client.get("/health")
        results.append(("GET /health", r.status_code, "ok" if r.status_code == 200 else r.text[:120]))

        r = client.post("/auth/login", json={"email": email, "password": password})
        results.append(("POST /auth/login", r.status_code, ""))
        if r.status_code != 200:
            print("Login failed:", r.text)
            for name, code, note in results:
                print(f"  {code}  {name}  {note}")
            sys.exit(1)
        token = r.json()["access_token"]

        h = _hdr(token)

        # --- Read-only (fast) ---
        for method, path, name in [
            ("GET", "/api/v1/blockers", "list blockers"),
            ("GET", "/api/v1/sprint/current", "sprint status"),
            ("GET", "/api/v1/sprint/draft", "sprint draft"),
            ("GET", "/api/v1/reports/current", "report current"),
            ("GET", "/api/v1/reports/history", "reports history"),
            ("GET", "/api/v1/voice/context", "voice context"),
            ("GET", "/api/v1/voice/transcripts", "call transcripts"),
        ]:
            r = client.request(method, path, headers=h)
            ok = r.status_code in (200, 404)
            note = ""
            if r.status_code == 404:
                note = "(no draft/report yet — OK)"
            results.append((f"{method} {path}", r.status_code, note if ok else r.text[:200]))

        if args.slow:
            print("\n--- Slow / LLM / integration calls (may take 30–120s each) ---\n")
            slow_routes = [
                ("POST", "/api/v1/standup/generate", {}, "standup generate"),
                ("POST", "/api/v1/blockers/scan", {}, "blocker scan"),
                ("POST", "/api/v1/sprint/draft/generate", {}, "sprint draft generate"),
            ]
            for method, path, body, label in slow_routes:
                r = client.request(method, path, headers=h, json=body)
                results.append(
                    (
                        f"{method} {path} ({label})",
                        r.status_code,
                        r.text[:300] if r.status_code >= 400 else "ok",
                    ),
                )

    print("PilotPM workflow smoke test\n" + "=" * 50)
    for name, code, note in results:
        ok = code in (200, 404)
        status = "OK" if ok else "!!"
        print(f"[{status}] {code:3d}  {name}  {note}")

    bad = [x for x in results if x[1] >= 500]
    if bad:
        print("\n5xx on:", [x[0] for x in bad], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
