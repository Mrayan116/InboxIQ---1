"""
Provider factory — the single place that decides which LLM backend runs.

Why a factory instead of importing GroqProvider everywhere: services should
depend on `get_llm_provider()`, not on a concrete class. This function is
also the natural place to add caching, retries-with-fallback (e.g. "try
Groq, fall back to OpenAI on 429"), or per-feature provider overrides later
without touching feature code.
"""

from functools import lru_cache

from app.core.config import settings
from app.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "groq":
        from app.llm.groq_provider import GroqProvider

        return GroqProvider()

    if settings.llm_provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider()

    if settings.llm_provider == "gemini":
        raise NotImplementedError(
            "Gemini provider not yet implemented — add app/llm/gemini_provider.py "
            "following the same pattern as GroqProvider, then register it here."
        )

    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
