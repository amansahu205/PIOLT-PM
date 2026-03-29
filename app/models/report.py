# app/models/report.py
"""F-004 status report API models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StatusReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    week_id: str = ""
    subject: str = ""
    body: str = ""
    hex_embed_url: str | None = None
    status: str = "draft"
    sent_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class EditReportBody(BaseModel):
    body: str = Field(..., min_length=1)


class SendResult(BaseModel):
    ok: bool = True
    message: str = ""
    staged_action: dict[str, Any] | None = None
