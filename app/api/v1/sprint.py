# app/api/v1/sprint.py
"""F-003 Sprint Autopilot — thin router → SprintService."""

from fastapi import APIRouter, Depends, HTTPException, status

import structlog

from app.dependencies import get_current_user, get_db_dep
from app.models.sprint import (
    SprintApprovalResult,
    SprintPlan,
    SprintStatus,
    UpdateDraftTicketsRequest,
)
from app.services.sprint_service import SprintService

log = structlog.get_logger()
router = APIRouter()


@router.get("/current", response_model=SprintStatus)
async def get_current_sprint(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Current sprint status from Monday.com (live board or demo snapshot)."""
    try:
        return await SprintService.get_current_sprint(db)
    except Exception as e:
        log.error("sprint.current_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to load current sprint")


@router.get("/draft", response_model=SprintPlan)
async def get_sprint_draft(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Latest AI sprint draft from MongoDB."""
    draft = await SprintService.get_draft(db)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sprint draft — use POST /draft/generate first",
        )
    return draft


@router.post("/draft/generate", response_model=SprintPlan)
async def generate_sprint_draft(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Generate a new sprint plan with K2 Think V2 (task=sprint) and persist as draft."""
    try:
        return await SprintService.generate_draft(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("sprint.generate_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Sprint draft generation failed")


@router.patch("/draft/tickets", response_model=SprintPlan)
async def patch_sprint_draft_tickets(
    body: UpdateDraftTicketsRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Update ticket selection/assignment; recomputes used capacity and utilization %."""
    try:
        return await SprintService.update_draft_tickets(body.tickets, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("sprint.patch_tickets_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update sprint draft")


@router.post("/approve", response_model=SprintApprovalResult)
async def approve_sprint(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Approve draft and stage Monday.com + calendar actions in the review queue."""
    try:
        return await SprintService.approve_sprint(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("sprint.approve_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Sprint approval failed")
