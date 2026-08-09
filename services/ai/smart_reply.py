"""
Feature 2: Smart Reply Generator.

Takes the user's WritingPreference (Feature 9) as input so generated
replies aren't generic -- they reflect the user's configured tone by
default, while still offering the three requested style variants.

Product invariant (from spec): InboxIQ never sends automatically. This
service only returns draft text; the actual Gmail send call lives in a
separate service (reply_sender.py) that is only invoked from an API route
requiring an explicit user action, never from this generation step.
"""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import SmartReplyResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """Generate three draft reply options to the given email: "professional",
"friendly", and "concise". Each should be a complete, ready-to-edit reply -- not a template
with placeholders unless truly necessary (e.g. a specific date the user must fill in).
Address the actual content of the email. Do not fabricate commitments, facts, or availability
the user hasn't stated. If the user has a preferred tone, lean the "professional" and "friendly"
variants toward it while keeping them clearly distinct from each other.

If prior messages in the thread are provided, use them: do not ask for information already
given earlier in the thread, and reflect any decisions or commitments already made. If urgency
or importance context is provided, let it shape tone (e.g. a critical/high-urgency email
generally warrants a more direct, timely-sounding response, not a leisurely one)."""


async def generate_smart_replies(
    llm: LLMProvider,
    *,
    original_subject: str,
    original_sender: str,
    original_body: str,
    user_preferred_tone: str | None = None,
    thread_history: list[dict] | None = None,
    importance_context: str | None = None,
) -> SmartReplyResult:
    preference_note = (
        f"The user's preferred writing tone is: {user_preferred_tone}."
        if user_preferred_tone
        else "No specific tone preference set."
    )

    history_note = ""
    if thread_history:
        formatted = "\n\n".join(f"From {m['sender']}: {m['body']}" for m in thread_history)
        history_note = f"\n\nPrior messages in this thread (oldest first):\n{formatted}"

    importance_note = f"\n\nContext: {importance_context}." if importance_context else ""

    user_prompt = (
        f"Original email:\nSubject: {original_subject}\nFrom: {original_sender}\n\n"
        f"{original_body}\n\n{preference_note}{importance_note}{history_note}"
    )
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=SmartReplyResult,
        temperature=0.5,  # a bit more creative latitude for natural-sounding drafts
        max_tokens=1500,
    )
