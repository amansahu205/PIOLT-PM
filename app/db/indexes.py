# app/db/indexes.py
"""MongoDB indexes — run on startup."""


async def ensure_indexes(db) -> None:
    # Context snapshots — TTL 1 hour
    await db.project_context.create_index("refreshed_at", expireAfterSeconds=3600)

    # Blockers — query by severity + status
    await db.blockers.create_index([("severity", 1), ("status", 1)])
    await db.blockers.create_index("engineer")
    await db.blockers.create_index("detected_at")

    # Review queue — query pending actions
    await db.review_queue.create_index([("status", 1), ("created_at", -1)])
    await db.review_queue.create_index("workflow_type")

    # Standup digests — TTL 7 days
    await db.standup_digests.create_index("generated_at", expireAfterSeconds=604800)

    # Voice transcripts — TTL 30 days
    await db.call_transcripts.create_index("called_at", expireAfterSeconds=2592000)
    await db.call_transcripts.create_index("call_sid", unique=False)

    # Sprint plans
    await db.sprint_plans.create_index([("sprint_number", -1)])
    await db.sprint_plans.create_index("status")

    # Status reports — current week + history
    await db.status_reports.create_index([("week_id", -1), ("updated_at", -1)])
    await db.status_reports.create_index("status")
