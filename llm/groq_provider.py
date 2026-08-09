"""
Groq adapter — implements LLMProvider.

Why Groq for dev: free tier with generous rate limits, and their inference
is fast (LPU hardware), which matters for features like tone analysis that
should feel near-instant while a user is typing an email. Uses Llama 3.3
70B by default — strong enough for summarization/classification tasks.

Swap-out note: this file only exists so `LLMProvider` has an implementation.
Nothing outside `app/llm/` should import `groq` directly.
"""

from groq import AsyncGroq

from app.core.config import settings
from app.core.logging import get_logger
from app.llm.base import LLMResponse

logger = get_logger(__name__)


class GroqProvider:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            logger.warning(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
            )
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            model=self._model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )
