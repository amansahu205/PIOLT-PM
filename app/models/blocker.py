from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DismissRequest(BaseModel):
    reason: str = ""


class BlockerCard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    engineer: str = ""
    severity: str = ""
    type: str = ""
    description: str = ""
    blocked_for: str = ""
    evidence: str = ""
    resolver: str = ""
    draft_ping: str = ""
    status: str = "active"
    detected_at: datetime | None = None
    dismissed_reason: str | None = None
    updated_at: datetime | None = None
