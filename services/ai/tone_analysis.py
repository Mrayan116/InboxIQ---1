"""Feature 3: Tone Analysis -- runs on outgoing drafts before send."""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import ToneAnalysisResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """Analyze the tone of this outgoing email draft the user is about to send.
Identify the detected tone (e.g. professional, aggressive, passive, friendly, confident, formal),
list specific concerns if any (e.g. "line 2 could read as passive-aggressive"), and give
concrete, actionable suggestions to improve clarity and professionalism. If the email is already
well-written, say so plainly and keep concerns/suggestions empty rather than inventing nitpicks."""


async def analyze_tone(llm: LLMProvider, *, draft_body: str, recipient_context: str | None = None) -> ToneAnalysisResult:
    context_note = f"Recipient context: {recipient_context}\n\n" if recipient_context else ""
    user_prompt = f"{context_note}Draft:\n{draft_body}"
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=ToneAnalysisResult,
        temperature=0.2,
    )
