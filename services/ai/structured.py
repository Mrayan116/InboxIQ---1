"""
Shared helper: call the LLM in JSON mode and validate the result against a
Pydantic schema.

Why centralize this: every AI feature follows the same pattern (prompt in,
JSON out, validate, retry once on failure). Duplicating that in 8 services
invites drift. One retry is included because LLMs occasionally return
near-valid JSON (trailing comma, etc.) — a single retry with a stricter
reminder resolves most of these cheaply.
"""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger
from app.llm.base import LLMProvider

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMOutputError(Exception):
    """Raised when the model fails to produce valid structured output twice in a row."""


async def structured_complete(
    llm: LLMProvider,
    *,
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> T:
    json_instruction = (
        f"{system_prompt}\n\n"
        f"Respond with ONLY valid JSON matching this shape (no markdown fences, no prose):\n"
        f"{schema.model_json_schema()}"
    )

    last_error: Exception | None = None
    for attempt in (1, 2):
        response = await llm.complete(
            system_prompt=json_instruction,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        try:
            data = json.loads(response.text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Structured output validation failed (attempt %s): %s", attempt, e)
            last_error = e

    raise LLMOutputError(f"Model failed to produce valid {schema.__name__} JSON") from last_error
