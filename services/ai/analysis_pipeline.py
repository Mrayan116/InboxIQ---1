"""
Orchestrates the AI analysis pipeline for a single newly-synced email:
summarize, classify priority, extract action items, check phishing risk.

Why a pipeline module instead of calling each service from the Celery task
directly: the task (Stage 4/workers) should stay a thin trigger; the actual
"what does 'analyze an email' mean" logic belongs here where it's testable
without Celery running at all.

Calls run concurrently (not sequentially) since they're independent LLM
calls against the same email -- this roughly divides total latency by 4
instead of summing it.
"""

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.models.email import ActionItem, EmailCategory, EmailMessage, Priority
from app.services.ai.action_items import extract_action_items
from app.services.ai.importance import classify_importance
from app.services.ai.phishing import analyze_phishing_risk
from app.services.ai.priority import classify_priority
from app.services.ai.summarizer import summarize_email

logger = get_logger(__name__)


async def analyze_email(
    session: AsyncSession,
    llm: LLMProvider,
    message: EmailMessage,
    *,
    sender_is_known_contact: bool = False,
) -> None:
    summary_task = summarize_email(llm, subject=message.subject, sender=message.sender, body=message.body_text)
    priority_task = classify_priority(
        llm,
        subject=message.subject,
        sender=message.sender,
        body=message.body_text,
        sender_is_known_contact=sender_is_known_contact,
    )
    action_items_task = extract_action_items(
        llm,
        subject=message.subject,
        body=message.body_text,
        received_at_iso=message.received_at.isoformat(),
    )
    phishing_task = analyze_phishing_risk(
        llm,
        subject=message.subject,
        sender=message.sender,
        sender_domain=message.sender_domain,
        body=message.body_text,
    )
    importance_task = classify_importance(
        llm,
        subject=message.subject,
        sender=message.sender,
        body=message.body_text,
        sender_is_known_contact=sender_is_known_contact,
    )

    results = await asyncio.gather(
        summary_task, priority_task, action_items_task, phishing_task, importance_task,
        return_exceptions=True,
    )
    summary, priority, action_items, phishing, importance = results

    if isinstance(summary, BaseException):
        logger.error("Summarization failed for message %s: %s", message.id, summary)
    else:
        message.ai_summary_short = summary.short_summary
        message.ai_summary_detailed = summary.detailed_summary
        message.ai_summary_bullets = json.dumps(summary.bullet_points)

    if isinstance(priority, BaseException):
        logger.error("Priority classification failed for message %s: %s", message.id, priority)
    else:
        try:
            message.priority = Priority(priority.priority.lower())
        except ValueError:
            logger.warning("Unrecognized priority value %r for message %s", priority.priority, message.id)
        message.priority_reason = priority.reason

    if isinstance(phishing, BaseException):
        logger.error("Phishing analysis failed for message %s: %s", message.id, phishing)
    else:
        message.is_phishing_suspected = phishing.is_suspicious
        message.phishing_reason = phishing.explanation

    if isinstance(importance, BaseException):
        logger.error("Importance classification failed for message %s: %s", message.id, importance)
    else:
        try:
            message.category = EmailCategory(importance.category.lower())
        except ValueError:
            logger.warning("Unrecognized category value %r for message %s", importance.category, message.id)
        message.importance_score = importance.importance_score
        message.importance_positive_signals = json.dumps(importance.positive_signals)
        message.importance_negative_signals = json.dumps(importance.negative_signals)

    message.analyzed_at = datetime.now(timezone.utc)
    session.add(message)

    if not isinstance(action_items, BaseException):
        for item in action_items.action_items:
            due = None
            if item.due_date:
                try:
                    due = datetime.fromisoformat(item.due_date)
                except ValueError:
                    pass
            session.add(
                ActionItem(
                    user_id=message.user_id,
                    email_message_id=message.id,
                    description=item.description,
                    due_date=due,
                )
            )
    else:
        logger.error("Action item extraction failed for message %s: %s", message.id, action_items)

    await session.commit()
