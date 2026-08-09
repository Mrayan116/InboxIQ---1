"""
LLM provider abstraction.

Why this exists: every AI feature in InboxIQ (summarization, tone analysis,
smart reply, phishing detection...) needs to call "some LLM" with a prompt
and get text back. If those features import `groq` or `openai` directly,
switching providers means touching every feature file, and unit-testing
those features means real API calls.

Instead, features depend on this `LLMProvider` Protocol. Adapters
(GroqProvider, OpenAIProvider, GeminiProvider) implement it. main.py wires
up whichever one `settings.llm_provider` points to. Tests can inject a
FakeProvider that returns canned responses instantly and for free.

This is the Strategy pattern applied to LLM calls.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    """Any LLM backend must implement this to be usable by InboxIQ services."""

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Run a single-turn completion.

        json_mode=True signals the provider to constrain output to valid
        JSON where supported — used by features like action-item extraction
        that need structured output, not prose.
        """
        ...
