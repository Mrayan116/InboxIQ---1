"""
Health & wiring-verification routes.

The `/health/llm` route is not a real product feature — it exists so that
once you drop a Groq API key into .env, you can hit one endpoint and confirm
the entire config -> factory -> provider -> API chain works before we build
any real AI feature on top of it.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_llm_dep
from app.llm.base import LLMProvider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/llm")
async def health_llm(llm: LLMProvider = Depends(get_llm_dep)) -> dict:
    response = await llm.complete(
        system_prompt="You are a terse assistant.",
        user_prompt="Reply with exactly: pong",
        max_tokens=10,
    )
    return {"provider_reachable": True, "model": response.text and response.model}
