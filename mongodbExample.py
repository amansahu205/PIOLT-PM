#!/usr/bin/env python3
"""
Minimal MongoDB Atlas example for PilotPM-style “engineering activity” data.

Why this file exists: prove your Atlas URI, user, and network rules work before relying
on the FastAPI app. It uses PyMongo synchronously so beginners can follow a straight line:
connect → write → read → close.

Install (once, from this repository root — pulls deps from pyproject.toml):
    uv sync

Run:
    uv run python mongodbExample.py

The connection string must come from the environment or a local config file — never hardcoded.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Repo root is the directory containing this script (project root).
_ROOT = Path(__file__).resolve().parent

# Same database name as PilotPM; separate collection so we do not touch app collections.
_DB_NAME = "pilotpm"
_COLLECTION = "example_engineering_events"


def load_uri() -> str:
    """
    Atlas URIs belong in env vars or an untracked file — not in source control.

    We load `.env` from the repo root so it matches how you run the API locally.
    """
    load_dotenv(_ROOT / ".env")
    uri = (os.environ.get("MONGODB_URI") or "").strip()
    if uri:
        return uri

    local = _ROOT / "mongodb.local.json"
    if local.is_file():
        cfg = json.loads(local.read_text(encoding="utf-8"))
        uri = (cfg.get("MONGODB_URI") or "").strip()
        if uri:
            print(f"[config] Using MONGODB_URI from {local.name}")
            return uri

    print(
        "Set MONGODB_URI in .env or create mongodb.local.json with "
        '{"MONGODB_URI": "..."} at the repo root.',
        file=sys.stderr,
    )
    sys.exit(1)


def build_documents() -> list[dict[str, object]]:
    """
    Ten rows that look like a PM feed: merges, deploys, standups, etc.

    `occurred_at` is a real BSON datetime with distinct values (staggered by hour)
    so sorting “most recent first” is meaningful.
    """
    now = datetime.now(UTC)
    base: list[dict[str, str]] = [
        {"type": "pr_merged", "title": "Auth middleware refactor", "engineer": "Alex"},
        {"type": "deploy", "title": "Staging release v0.3.2", "engineer": "Jordan"},
        {"type": "ticket_done", "title": "Fix pagination on backlog view", "engineer": "Sarah"},
        {"type": "standup", "title": "Daily sync — no blockers", "engineer": "Mike"},
        {"type": "incident", "title": "API latency spike investigated", "engineer": "Alex"},
        {"type": "pr_opened", "title": "Feature: export sprint CSV", "engineer": "Jordan"},
        {"type": "ticket_done", "title": "Monday board sync job", "engineer": "Sarah"},
        {"type": "review", "title": "Security review for OAuth flow", "engineer": "Mike"},
        {"type": "deploy", "title": "Hotfix: null guard in digest", "engineer": "Alex"},
        {"type": "standup", "title": "Daily sync — waiting on keys", "engineer": "Sarah"},
    ]
    out: list[dict[str, object]] = []
    for i, row in enumerate(base):
        out.append(
            {
                **row,
                "occurred_at": now - timedelta(hours=i),
                "source": "mongodbExample.py",
            },
        )
    return out


def main() -> None:
    print("--- MongoDB Atlas + Python (PyMongo) ---\n")

    uri = load_uri()
    client = MongoClient(uri, serverSelectionTimeoutMS=10_000)

    try:
        # Confirms DNS + credentials + network access (Atlas IP allowlist).
        client.admin.command("ping")
        print("[ok] Ping succeeded — driver reached your cluster.\n")

        col = client[_DB_NAME][_COLLECTION]

        # Remove prior runs so repeat executions stay predictable.
        removed = col.delete_many(
            {
                "source": {
                    "$in": [
                        "mongodbExample.py",
                        "scripts/mongo_smoke.py",
                        "mongodbExample.mjs",
                    ],
                },
            },
        )
        if removed.deleted_count:
            print(f"[info] Removed {removed.deleted_count} old example document(s).\n")

        print(f"[step] Inserting 10 documents into {_DB_NAME}.{_COLLECTION} ...")
        docs = build_documents()
        insert_result = col.insert_many(docs)
        print(f"[ok] Inserted {len(insert_result.inserted_ids)} document(s).\n")

        print("[step] Five most recent rows (sort by occurred_at, newest first):\n")
        recent = list(col.find().sort("occurred_at", -1).limit(5))
        for i, doc in enumerate(recent, 1):
            print(f"--- #{i} ---")
            print(json.dumps(doc, indent=2, default=str))
            print()

        if not recent:
            raise RuntimeError("Expected documents after insert.")

        first_id = insert_result.inserted_ids[0]
        print("[step] Fetch one document by its _id:\n")
        one = col.find_one({"_id": first_id})
        print(json.dumps(one, indent=2, default=str))
        print()

    except PyMongoError as e:
        print(f"[error] MongoDB driver error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()
        print("[ok] Connection closed.")


if __name__ == "__main__":
    main()
