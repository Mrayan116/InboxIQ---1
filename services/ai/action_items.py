"""Feature 4: Action Item Extraction."""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import ActionItemExtractionResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """Extract concrete action items the recipient needs to take from this email.
Only extract items the recipient must DO -- not things the sender is doing, and not general
information. If a deadline is explicitly stated or clearly implied (e.g. "by Friday"), include
it as an ISO 8601 date relative to the email's received date if given, otherwise omit due_date.
If there are no action items, return an empty list. Do not invent action items."""


async def extract_action_items(
    llm: LLMProvider, *, subject: str, body: str, received_at_iso: str
) -> ActionItemExtractionResult:
    user_prompt = f"Email received: {received_at_iso}\nSubject: {subject}\n\nBody:\n{body}"
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ActionItemExtractionResult,
        temperature=0.1,
    )
