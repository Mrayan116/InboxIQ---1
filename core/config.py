"""
Centralized application configuration.

Why: hard-coded config scattered across files is the #1 cause of "works on my
machine" bugs. Pydantic Settings gives us type-validated env vars, sane
defaults for local dev, and a single object (`settings`) injected wherever
config is needed. Fails fast at startup if something required is missing.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "InboxIQ"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://inboxiq:inboxiq@localhost:5432/inboxiq"
    )

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --- Auth ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    jwt_secret_key: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- LLM Provider ---
    # "groq" is free-tier friendly for development. Swap to "openai" or
    # "gemini" in prod by changing this one value — no code changes.
    llm_provider: Literal["groq", "openai", "gemini"] = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # --- Logging ---
    log_level: str = "INFO"

    # --- CORS ---
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse env vars once per process, not per request."""
    return Settings()


settings = get_settings()
