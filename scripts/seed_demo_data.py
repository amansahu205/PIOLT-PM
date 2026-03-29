#!/usr/bin/env python3
"""Seed PilotPM demo data into MongoDB (demo_github, demo_slack, demo_monday)."""

from __future__ import annotations

import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.db.mongo import close_mongo, connect_mongo, get_collection


def _iso(dt: datetime) -> str:
    return dt.replace(tzinfo=UTC).isoformat()


async def seed() -> None:
    await connect_mongo()

    now = datetime.now(UTC)

    def hours_ago(n: float) -> datetime:
        return now - timedelta(hours=n)

    # ── demo_github: commits + open PRs ─────────────────────────────────────
    gh = get_collection("demo_github")
    await gh.delete_many({})

    commits: list[dict] = []
    # Sarah + Tom: 4 commits each in the last 24h (recent activity)
    for i, author in enumerate(["Sarah Ali"] * 4 + ["Tom Kim"] * 4):
        commits.append(
            {
                "doc_type": "commit",
                "sha": f"{i+1:02x}{'a' * 38}"[:40],
                "author": author,
                "message": [
                    "feat: add payment webhook handler",
                    "fix: null check on session store",
                    "chore: bump deps for security patch",
                    "refactor: extract auth middleware",
                ][i % 4]
                if author == "Sarah Ali"
                else [
                    "feat: API keys rotation endpoint",
                    "test: cover edge cases for billing",
                    "docs: update README for deploy",
                    "perf: cache config lookup",
                ][i % 4],
                "committed_at": _iso(hours_ago(6 + i * 2)),  # spread in last ~24h
                "repo": "pilotpm/acme-api",
            }
        )
    # Mike: 4 commits, all older than 24h (inactivity signal)
    for i in range(4):
        commits.append(
            {
                "doc_type": "commit",
                "sha": f"{10+i:02x}{'b' * 38}"[:40],
                "author": "Mike Ross",
                "message": ["legacy: admin export", "fix: typo in logs", "chore: cleanup", "docs: internal wiki"][
                    i
                ],
                "committed_at": _iso(hours_ago(72 + i * 6)),  # 72–90+ hours ago
                "repo": "pilotpm/acme-api",
            }
        )

    prs: list[dict] = [
        {
            "doc_type": "pull_request",
            "number": 140,
            "author": "Tom Kim",
            "title": "feat: usage dashboard v1",
            "state": "open",
            "reviews": 2,
            "age_hours": 8,
            "url": "https://github.com/pilotpm/acme-api/pull/140",
        },
        {
            "doc_type": "pull_request",
            "number": 141,
            "author": "Tom Kim",
            "title": "fix: flaky test in CI",
            "state": "open",
            "reviews": 1,
            "age_hours": 18,
            "url": "https://github.com/pilotpm/acme-api/pull/141",
        },
        {
            "doc_type": "pull_request",
            "number": 142,
            "author": "Sarah Ali",
            "title": "chore: eslint config",
            "state": "open",
            "reviews": 1,
            "age_hours": 30,
            "url": "https://github.com/pilotpm/acme-api/pull/142",
        },
        {
            "doc_type": "pull_request",
            "number": 143,
            "author": "Sarah Ali",
            "title": "feat: OAuth scope expansion",
            "state": "open",
            "reviews": 0,
            "age_hours": 52,
            "url": "https://github.com/pilotpm/acme-api/pull/143",
        },
        {
            "doc_type": "pull_request",
            "number": 144,
            "author": "Mike Ross",
            "title": "docs: runbook for deploy",
            "state": "open",
            "reviews": 0,
            "age_hours": 12,
            "url": "https://github.com/pilotpm/acme-api/pull/144",
        },
    ]

    await gh.insert_many(commits + prs)

    # ── demo_slack: #engineering, last 48h ──────────────────────────────────
    slack = get_collection("demo_slack")
    await slack.delete_many({})

    slack_docs: list[dict] = []

    def slack_msg(
        user: str,
        text: str,
        hours_ago: float,
        channel: str = "#engineering",
    ) -> dict:
        ts = now - timedelta(hours=hours_ago)
        return {
            "channel": channel,
            "user": user,
            "text": text,
            "ts": _iso(ts),
        }

    # Required lines
    slack_docs.append(slack_msg("sarah_ali", "still waiting on those keys — blocked on prod deploy", 6.0))
    slack_docs.append(slack_msg("tom_kim", "waiting on API keys from infra before I can merge the gateway PR", 4.5))
    # Three PR review requests from tom_kim
    slack_docs.append(
        slack_msg(
            "tom_kim",
            "Could someone review PR #140? Need another pair of eyes on the usage dashboard.",
            10.0,
        )
    )
    slack_docs.append(
        slack_msg("tom_kim", "Ping on PR #141 — small CI fix, should be quick to review.", 20.0)
    )
    slack_docs.append(
        slack_msg(
            "tom_kim",
            "Review requested: https://github.com/pilotpm/acme-api/pull/142 — needs approval for eslint changes",
            28.0,
        )
    )

    # Fill to 30+ with realistic chatter
    filler_users = ["sarah_ali", "tom_kim", "mike_ross", "alex_dev", "jamie_ops"]
    filler_texts = [
        "deployed staging looks green",
        "rolling back feature flag FF-204",
        "anyone seen the latency spike on /v1/checkout?",
        "pairing after lunch on the migration",
        "I'll grab the on-call ticket",
        "retro notes in Notion",
        "can we bump the timeout on the worker queue?",
        "LGTM on the schema change",
        "checking Atlas metrics now",
        "incident channel is quiet today",
        "merged to main, tagging v0.9.2",
        "standup async — shipping invoices today",
        "blocked on schema review from platform",
        "starting load test in 10m",
        "fixing flaky test locally",
        "who owns the webhook retries?",
        "oauth redirect URL updated in staging",
        "npm audit clean on frontend",
        "docker build cache is huge again",
        "scaling the preview envs down overnight",
        "paging @sarah_ali for the keys thread",
        "threaded reply: +1 on the approach",
        "Monday board sync looks off for SP-12",
        "I'll open a ticket for the backlog cleanup",
        "voice call with vendor at 3pm",
        "canary at 10% — watching error rates",
    ]
    random.seed(42)
    for i, text in enumerate(filler_texts):
        u = filler_users[i % len(filler_users)]
        slack_docs.append(slack_msg(u, text, float(random.uniform(0.5, 47.0))))

    # Extra messages to comfortably exceed 30
    for i in range(15):
        slack_docs.append(
            slack_msg(
                filler_users[i % len(filler_users)],
                f"noise message {i+1}: CI pipeline #{420 + i} passed",
                float(random.uniform(1.0, 46.0)),
            )
        )

    await slack.insert_many(slack_docs)

    # ── demo_monday: Sprint 24 board + tickets ───────────────────────────────
    mon = get_collection("demo_monday")
    await mon.delete_many({})

    monday_docs: list[dict] = [
        {
            "doc_type": "sprint_snapshot",
            "sprint_name": "Sprint 24",
            "total_tickets": 14,
            "in_progress_count": 6,
            "board_id": "board_demo_001",
            "updated_at": _iso(now),
        }
    ]

    statuses = (["in_progress"] * 6) + (["todo"] * 4) + (["done"] * 4)
    random.shuffle(statuses)
    for i in range(14):
        monday_docs.append(
            {
                "doc_type": "ticket",
                "sprint": "Sprint 24",
                "ticket_id": f"SP-24-{i+1:02d}",
                "name": [
                    "Payment gateway hardening",
                    "OAuth consent screen",
                    "Webhook retries",
                    "Usage export CSV",
                    "Admin audit log",
                    "Rate limit tuning",
                    "Mobile SDK bump",
                    "Docs: API reference",
                    "Bug: duplicate invoice",
                    "Feature: team roles",
                    "Chore: dependency sweep",
                    "Spike: GraphQL feasibility",
                    "Tech debt: monolith split",
                    "Support: bulk refund tool",
                ][i],
                "status": statuses[i],
                "points": [3, 5, 2, 8, 3, 5, 2, 3, 1, 5, 2, 8, 13, 3][i],
            }
        )

    await mon.insert_many(monday_docs)

    await close_mongo()

    print("Seed complete.")
    print(f"  demo_github:  {len(commits)} commits + {len(prs)} PRs")
    print(f"  demo_slack:   {len(slack_docs)} messages")
    print(f"  demo_monday:  {len(monday_docs)} documents (1 sprint snapshot + 14 tickets)")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
