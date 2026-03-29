# app/api/v1/voice.py
"""
Twilio inbound call webhook — F-005.
ElevenLabs Conversational AI: we delegate TwiML to POST /v1/convai/twilio/register-call
so the Stream WebSocket URL and protocol match what Twilio expects.
"""

from fastapi import APIRouter, Depends, Request, Response

import structlog
from twilio.twiml.voice_response import VoiceResponse

from app.dependencies import get_current_user, get_db_dep
from app.services.voice_service import VoiceService

log = structlog.get_logger()
router = APIRouter()


@router.post("/webhook/inbound")
async def inbound_call(request: Request, db=Depends(get_db_dep)):
    """
    Twilio hits this URL when someone dials the PilotPM number (configure in Twilio Console:
    Phone Numbers → your number → Voice & Fax → A call comes in → Webhook POST).

    Public HTTPS URL required (e.g. Railway, ngrok); Twilio cannot reach localhost.

    We pass PilotPM context as a **prompt override** on register-call so the agent answers
    from live GitHub / Slack / Monday snapshot text.
    """
    form = await request.form()
    caller = str(form.get("From") or "")
    called = str(form.get("To") or "")
    call_sid = str(form.get("CallSid") or "")

    log.info("voice.inbound_call", caller=caller, called=called, call_sid=call_sid)

    try:
        ctx_bundle = await VoiceService.get_voice_context(db)
        agent_id = ctx_bundle["agent_id"]
        system_prompt = ctx_bundle["system_prompt"]

        await VoiceService.log_call_start(call_sid, caller or "unknown", db)

        twiml = await VoiceService.get_twiml_for_twilio_inbound(
            from_number=caller,
            to_number=called,
            agent_id=agent_id,
            system_prompt=system_prompt,
        )
        return Response(content=twiml, media_type="application/xml")
    except Exception as exc:
        log.exception("voice.inbound_failed", error=str(exc))
        vr = VoiceResponse()
        vr.say(
            "Sorry, PilotPM voice is temporarily unavailable. Please try again later.",
            voice="Polly.Joanna",
        )
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")


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
