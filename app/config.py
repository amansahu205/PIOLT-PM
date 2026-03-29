# app/config.py
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "development"

    # Auth (hardcoded demo — no user DB)
    DEMO_EMAIL: str
    DEMO_PASSWORD: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # MongoDB
    MONGODB_URI: str = Field(..., min_length=1, description="MongoDB connection URI (required)")
    MONGODB_DB: str = "pilotpm"

    # AI — Lava gateway (docs index: https://lava.so/docs/llms.txt)
    # Forward proxy + auth: https://lava.so/docs/gateway/forward-proxy.md
    # Forward POST API: https://lava.so/docs/api-reference/core-endpoints/forward-post-request.md
    # Secret key (aks_live_...): LAVA_API_KEY or LAVA_SECRET_KEY — see quickstart-track.md
    LAVA_API_KEY: str = Field(
        ...,
        validation_alias=AliasChoices("LAVA_API_KEY", "LAVA_SECRET_KEY"),
    )
    # POST {LAVA_BASE}/v1/forward?u=<upstream URL> — https://lava.so/docs/get-started/quickstart-track.md
    LAVA_BASE: str = "https://api.lava.so"
    LAVA_FORWARD_UPSTREAM: str = "https://api.openai.com/v1/chat/completions"
    # Must match the upstream API (OpenAI IDs when LAVA_FORWARD_UPSTREAM is OpenAI).
    LAVA_MODEL_PRIMARY: str = "gpt-4o-mini"
    LAVA_MODEL_FALLBACK: str = "gpt-4o"

    # Optional: Gemini direct fallback if Lava fails — google-genai SDK (see ai.google.dev/gemini-api/docs)
    # Terms: https://ai.google.dev/gemini-api/terms — override GEMINI_MODEL to pin a stable release.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3-flash-preview"

    # K2 Think V2 — MBZUAI IFM (YHack / api.k2think.ai)
    K2_API_KEY: str
    K2_API_BASE: str = "https://api.k2think.ai"
    K2_MODEL: str = "MBZUAI-IFM/K2-Think-v2"

    # Integrations
    GITHUB_TOKEN: str
    GITHUB_REPO: str = "pilotpm/acme-api"  # owner/repo — e.g. amansahu205/acme-api
    SLACK_BOT_TOKEN: str
    # Engineering/context channel: Slack channel ID (C…) or #channel-name — used for reads + blocker pings
    SLACK_ENGINEERING_CHANNEL: str = "#engineering"
    # Standup digest post target when staged to review queue
    SLACK_STANDUP_CHANNEL: str = "#standup-digest"
    MONDAY_API_KEY: str
    ELEVENLABS_API_KEY: str
    ELEVENLABS_AGENT_ID: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE: str
    HEX_API_KEY: str

    # Stakeholder emails (comma-separated)
    STAKEHOLDER_EMAILS: str = ""

    # Optional SMTP for GmailService (empty = send_email returns False)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # CORS — use JSON array in `.env`, e.g. ["http://localhost:3000","https://piolt-pm.vercel.app"]
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://piolt-pm.vercel.app",
        ],
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
