"""
Feature 7: Phishing Detection.

Important product behavior from the spec: explain WHY an email looks
suspicious rather than just slapping an "unsafe" label on it. This is
enforced by the schema (`explanation` is required, not optional) and the
prompt explicitly asks for reasoning grounded in specific signals rather
than a bare verdict.
"""

from app.llm.base import LLMProvider
from app.schemas.ai_outputs import PhishingAnalysisResult
from app.services.ai.structured import structured_complete

SYSTEM_PROMPT = """You are a security-conscious email analyst. Evaluate this email for phishing
indicators: urgency/fear tactics, requests for credentials or payment info, mismatched or
lookalike sender domains, suspicious links (described, since you cannot click them), poor
grammar inconsistent with claimed sender, and impersonation of known brands or coworkers.
Be conservative: only flag as suspicious if there are genuine, specific signals -- do not flag
routine business emails, legitimate marketing, or normal password-reset emails the user likely
requested themselves. Always explain your reasoning in plain English, even when not suspicious."""


async def analyze_phishing_risk(
    llm: LLMProvider, *, subject: str, sender: str, sender_domain: str, body: str
) -> PhishingAnalysisResult:
    user_prompt = (
        f"Subject: {subject}\nFrom: {sender} (domain: {sender_domain})\n\nBody:\n{body}"
    )
    return await structured_complete(
        llm,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=PhishingAnalysisResult,
        temperature=0.1,
    )
