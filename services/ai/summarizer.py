"""
Feature 1: AI Email Summarization.

One LLM call produces all three summary formats at once (short/detailed/
bullets) rather than three separate calls — cheaper, faster, and the
formats stay consistent with each other since they come from the same
reasoning pass.
"""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import SummaryResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """You are an email summarization assistant embedded in an email client.
Summarize the given email accurately and neutrally. Never invent details not present
in the email. If the email is short enough that summarizing feels redundant, still
provide all three formats, keeping them appropriately brief."""


async def summarize_email(llm: LLMProvider, *, subject: str, sender: str, body: str) -> SummaryResult:
    user_prompt = f"Subject: {subject}\nFrom: {sender}\n\nBody:\n{body}"
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=SummaryResult,
    )
