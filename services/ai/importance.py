"""
AI Inbox Organization: classifies each email into one of five categories
and produces a 0-100 importance score with explicit positive/negative
signals -- not a bare number. This is deliberately a separate axis from
`priority` (Feature 5, critical/high/medium/low urgency): priority answers
"how soon," this answers "how much does this matter and why," which is
what the dashboard/briefing and inbox filtering need.

Kept as one LLM call (not two) since category and importance score are
reasoned from the same evidence -- splitting them would double latency and
cost for no accuracy gain, and risks the two outputs disagreeing with each
other (e.g. "important" but a low score).
"""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import ImportanceResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """You organize a busy professional's inbox. For the given email, assign:

1. category -- exactly one of:
   - important: significant personal/professional relevance, no immediate action needed
   - requires_action: the recipient must do something (reply, approve, submit, pay, schedule)
   - informational: relevant but purely FYI, no action and not especially significant
   - newsletter_marketing: bulk/promotional/subscription content
   - low_value: automated notifications, spam-adjacent, or content with essentially no relevance

2. importance_score -- 0-100. Roughly: 80-100 truly important or urgent action needed;
   50-79 worth reading soon; 20-49 low urgency FYI; 0-19 newsletters/automated/garbage.

3. positive_signals -- concrete reasons raising importance (e.g. "from a known frequent
   contact", "contains an explicit deadline", "requires a direct response", "mentions an
   active project by name"). Empty list if none apply.

4. negative_signals -- concrete reasons lowering importance (e.g. "automated/no-reply sender",
   "marketing or promotional content", "mass/bulk email", "no action or response needed").
   Empty list if none apply.

Ground every signal in something actually present in the email -- do not invent signals."""


async def classify_importance(
    llm: LLMProvider,
    *,
    subject: str,
    sender: str,
    body: str,
    sender_is_known_contact: bool,
) -> ImportanceResult:
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
        schema=ImportanceResult,
        temperature=0.1,
    )
