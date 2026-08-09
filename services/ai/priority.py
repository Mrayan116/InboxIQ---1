"""
Feature 5: AI Priority Detection.

Deliberately takes `sender_is_known_contact` as an explicit signal rather
than asking the LLM to guess sender importance from the email address
alone — the app has ground truth (has this user emailed this sender
before?) that the LLM doesn't. Combining a real signal with LLM judgment
beats asking the LLM to do both.
"""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import PriorityResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """You classify email urgency for a busy professional's inbox.
Levels: critical (needs action today, e.g. deadline today/tomorrow, urgent request from
important contact), high (needs action this week), medium (should be read but not urgent),
low (newsletters, FYI, no action needed).
Base your judgment on explicit deadlines, urgency language, and the sender signal provided
-- not on assumptions about topics you weren't told are important."""


async def classify_priority(
    llm: LLMProvider,
    *,
    subject: str,
    sender: str,
    body: str,
    sender_is_known_contact: bool,
) -> PriorityResult:
    user_prompt = (
        f"Subject: {subject}\n"
        f"From: {sender}\n"
        f"Sender is a known/frequent contact: {sender_is_known_contact}\n\n"
        f"Body:\n{body}"
    )
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=PriorityResult,
        temperature=0.1,  # classification tasks want low variance
    )
