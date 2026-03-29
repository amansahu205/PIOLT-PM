# app/models/sprint.py
"""F-003 Sprint Autopilot — request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SprintTicket(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    score: int = Field(default=0, ge=0, le=100)
    reasoning: str = ""
    estimated_pts: float = 0
    assigned_to: str = ""
    assignment_reason: str = ""
    priority: str = "P3"
    selected: bool = True


class SprintPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    status: str = "draft"
    sprint_number: int = 0
    sprint_name: str = ""
    total_capacity_pts: float = 0
    used_capacity_pts: float = 0
    utilization_pct: float = 0
    tickets: list[SprintTicket] = Field(default_factory=list)
    deferred: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: str | None = None
    agent_model: str | None = None  # e.g. MBZUAI-IFM/K2-Think-v2


class SprintStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sprint_name: str | None = None
    velocity_pct: int = 0
    board_id: str | None = None
    tickets: list[dict[str, Any]] = Field(default_factory=list)
    in_progress_count: int | None = None
    updated_at: str | None = None


class UpdateDraftTicketsRequest(BaseModel):
    tickets: list[SprintTicket]


class SprintApprovalResult(BaseModel):
    message: str
    staged_actions: list[dict[str, Any]]
    agent_model: str = "k2-think-v2"
