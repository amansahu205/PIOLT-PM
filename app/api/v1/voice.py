# app/api/v1/voice.py
"""
Twilio inbound call webhook — F-005.
ElevenLabs Conversational AI handles audio; this route returns TwiML to bridge the stream.
"""

from fastapi import APIRouter, Depends, Request, Response

import structlog
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse

from app.dependencies import get_current_user, get_db_dep
from app.services.voice_service import VoiceService

log = structlog.get_logger()
router = APIRouter()


@router.post("/webhook/inbound")
async def inbound_call(request: Request, db=Depends(get_db_dep)):
    """
    Twilio hits this URL when someone dials the PilotPM number.
    Returns TwiML that connects the call to ElevenLabs Conversational AI via WebSocket.
    """
    form = await request.form()
    caller = str(form.get("From") or "unknown")
    call_sid = str(form.get("CallSid") or "")

    log.info("voice.inbound_call", caller=caller, call_sid=call_sid)

    context = await VoiceService.get_voice_context(db)
    await VoiceService.log_call_start(call_sid, caller, db)

    agent_id = context["agent_id"]
    system_prompt = context["system_prompt"]

    twiml = VoiceResponse()
    connect = Connect()
    stream = Stream(
        url=f"wss://api.elevenlabs.io/v1/convai/call?agent_id={agent_id}",
    )
    stream.parameter(name="agent_context", value=system_prompt)
    connect.append(stream)
    twiml.append(connect)

    return Response(content=str(twiml), media_type="application/xml")


@router.get("/context")
async def get_voice_context(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Current condensed context used to build the voice system prompt (dashboard)."""
    return await VoiceService.get_voice_context_summary(db)


@router.get("/transcripts")
async def get_transcripts(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_dep),
):
    """Recent call log rows from MongoDB (last N)."""
    return await VoiceService.get_transcripts(limit=limit, db=db)
