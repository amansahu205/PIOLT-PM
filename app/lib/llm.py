# app/lib/llm.py
"""
Central LLM client. All AI calls go through here.
Never call models directly from route handlers or agents.

Routing:
  task = "sprint" | "backlog"  →  K2 first; on failure → same chain below
  Main path                    →  Lava (LAVA_MODEL_PRIMARY), then Lava again (LAVA_MODEL_FALLBACK)
  Last resort                  →  Gemini via GEMINI_API_KEY (google-genai) if set and both Lava calls failed
  voice                        →  ElevenLabs (WebSocket, not here)

Lava: POST {LAVA_BASE}/v1/forward?u=<upstream>. Refs: gateway/forward-proxy.md,
api-reference/core-endpoints/forward-post-request.md, agents/route-traffic.md (under https://lava.so/docs/).
"""

import asyncio

import httpx
import structlog
from google import genai
from google.genai import types

from app.config import settings
from app.lib.cost import log_llm_cost

log = structlog.get_logger()

K2_BASE = settings.K2_API_BASE


def _lava_forward_url() -> str:
    return f"{settings.LAVA_BASE.rstrip('/')}/v1/forward"


def _k2_chat_url() -> str:
    return f"{K2_BASE.rstrip('/')}/v1/chat/completions"


# ─── Lava gateway (OpenAI-compatible body; upstream from LAVA_FORWARD_UPSTREAM) ─


async def call_via_lava(
    system: str,
    user: str,
    model: str,  # e.g. gpt-4o-mini when upstream is OpenAI; override via LAVA_MODEL_*
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> str:
    """All cloud LLM calls go through Lava forward — Bearer auth, payload is OpenAI chat format."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            _lava_forward_url(),
            params={"u": settings.LAVA_FORWARD_UPSTREAM},
            headers={
                "Authorization": f"Bearer {settings.LAVA_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        body = r.json()
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        log_llm_cost(
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
        return content


# ─── Google Gemini direct (optional last fallback) ─────────────────────────────


async def call_via_gemini(
    system: str,
    user: str,
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> str:
    """google-genai `generate_content` — only when Lava fails and GEMINI_API_KEY is set."""
    key = settings.GEMINI_API_KEY.strip()
    if not key:
        raise ValueError("GEMINI_API_KEY is empty")
    model = settings.GEMINI_MODEL.strip()

    def _sync_call() -> tuple[str, int, int]:
        # Preview / "thinking" models may use output budget before visible text; avoid tiny caps.
        out_cap = max(max_tokens, 256)
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=out_cap,
            ),
        )
        text = (resp.text or "").strip()
        if not text:
            raise ValueError("Gemini returned empty text")
        um = resp.usage_metadata
        inp = int(um.prompt_token_count or 0) if um else 0
        out = int(um.candidates_token_count or 0) if um else 0
        return text, inp, out

    text, input_tokens, output_tokens = await asyncio.to_thread(_sync_call)
    log_llm_cost(
        model=f"google/{model}",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    return text


# ─── K2 Think V2 direct (MBZUAI sponsor) ──────────────────────────────────────


async def call_k2(
    system: str,
    user: str,
    temperature: float = 0.0,  # reasoning model — keep low
    max_tokens: int = 8192,
) -> str:
    """Direct call to MBZUAI IFM K2 Think V2 (sprint + backlog). OpenAI-compatible JSON."""
    model_id = settings.K2_MODEL
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {settings.K2_API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            _k2_chat_url(),
            json=payload,
            headers=headers,
        )
        r.raise_for_status()
        body = r.json()
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        log_llm_cost(
            model=model_id,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
        log.info(
            "llm.k2",
            model=model_id,
            tokens_approx=len(content.split()),
        )
        return content


# ─── Unified router ────────────────────────────────────────────────────────────


async def call_ai(
    system: str,
    user: str,
    task: str = "general",  # "sprint" | "backlog" | "classify" | "general"
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> str:
    """
    Single entry point for all AI calls in PilotPM.
    Routes to correct model, falls back gracefully.
    """

    # Sprint and backlog → K2 Think V2 (MBZUAI sponsor, purpose-built reasoning)
    if task in ("sprint", "backlog"):
        try:
            return await call_k2(system, user, temperature=0.0, max_tokens=max_tokens)
        except Exception as e:
            log.warning("k2.failed", error=str(e), falling_back_to="lava_primary")

    last: Exception | None = None
    try:
        return await call_via_lava(
            system,
            user,
            model=settings.LAVA_MODEL_PRIMARY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        last = e
        log.warning("lava_primary.failed", error=str(e), falling_back_to="lava_fallback")

    try:
        return await call_via_lava(
            system,
            user,
            model=settings.LAVA_MODEL_FALLBACK,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        last = e
        log.warning("lava_fallback.failed", error=str(e))

    if settings.GEMINI_API_KEY.strip():
        try:
            log.warning("llm.using_gemini_direct_fallback")
            return await call_via_gemini(
                system, user, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as ge:
            log.error("gemini.fallback_failed", error=str(ge))
            raise last from ge

    if last is not None:
        raise last
    raise RuntimeError("call_ai: no provider succeeded")
