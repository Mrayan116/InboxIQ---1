"""
Feature 8: Email Simplifier.

Plain text in, plain text out -- no structured schema needed here since
the entire output IS the artifact (a rewritten email), not data to store
in typed fields.
"""

from app.llm.base import LLMProvider

SYSTEM_PROMPT = """Rewrite the given email in plain, simple English. Remove legal jargon,
business buzzwords, and unnecessarily complex phrasing while preserving every factual detail,
number, date, and commitment exactly. Do not shorten by omitting substantive content -- only
simplify the language. Return only the rewritten email, no preamble or explanation."""


async def simplify_email(llm: LLMProvider, *, original_body: str) -> str:
    response = await llm.complete(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=original_body,
        temperature=0.2,
        max_tokens=1500,
    )
    return response.text.strip()
