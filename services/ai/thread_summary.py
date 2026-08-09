"""Feature 6: Thread Summarization -- reasons over an entire conversation."""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import ThreadSummaryResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """You are given an entire email thread in chronological order. Produce:
a chronological timeline of key events, key decisions that were made, open questions that
remain unresolved, and a one-sentence current status. Ground everything in what was actually
written -- do not infer decisions or resolutions that weren't explicitly stated."""


async def summarize_thread(llm: LLMProvider, *, messages: list[dict]) -> ThreadSummaryResult:
    """
    `messages` is a list of {sender, sent_at, body} dicts in chronological order.
    """
    formatted = "\n\n---\n\n".join(
        f"From: {m['sender']} at {m['sent_at']}\n{m['body']}" for m in messages
    )
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=formatted,
        schema=ThreadSummaryResult,
        temperature=0.2,
        max_tokens=1500,
    )
