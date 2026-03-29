# app/api/v1/reports.py
"""F-004 status reports — thin router."""

from fastapi import APIRouter, Depends, HTTPException, status

import structlog

from app.dependencies import get_current_user, get_db_dep
from app.models.report import EditReportBody, SendResult, StatusReport
from app.services.report_service import ReportService

log = structlog.get_logger()
router = APIRouter()


@router.get("/current", response_model=StatusReport)
async def get_current_report(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """This week's report (draft or sent)."""
    doc = await ReportService.get_current(db)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report for this week yet",
        )
    return doc


@router.post("/generate", response_model=StatusReport)
async def generate_report(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Generate a new draft from context + LLM + optional Hex embed."""
    try:
        return await ReportService.generate_report(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("reports.generate_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.patch("/{report_id}/edit", response_model=StatusReport)
async def edit_report(
    report_id: str,
    body: EditReportBody,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Edit email body inline (draft only)."""
    try:
        return await ReportService.edit_report(report_id, body.body, db)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        log.error("reports.edit_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.post("/{report_id}/send", response_model=SendResult)
async def send_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Queue stakeholder email via review queue; marks report sent for this week."""
    try:
        return await ReportService.send_report(report_id, db)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        log.error("reports.send_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to queue send")


@router.get("/history", response_model=list[StatusReport])
async def report_history(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Past reports (default 4)."""
    return await ReportService.get_history(db, n=4)
