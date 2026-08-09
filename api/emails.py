import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_llm_dep
from app.core.database import get_db
from app.llm.base import LLMProvider
from app.models.email import EmailCategory, Priority
from app.models.user import User
from app.repositories.email_repository import EmailRepository
from app.repositories.user_repository import UserRepository
from app.schemas.api import EmailDetail, EmailListItem, SimplifyRequest, SyncTriggerResponse, ToneAnalysisRequest
from app.schemas.ai_outputs import SmartReplyResult, ToneAnalysisResult
from app.services.ai.simplifier import simplify_email
from app.services.ai.smart_reply import generate_smart_replies
from app.services.ai.thread_summary import summarize_thread
from app.services.ai.tone_analysis import analyze_tone
from app.workers.celery_app import celery_app
from app.workers.sync_tasks import sync_user_inbox
from celery.result import AsyncResult

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_sync(user: User = Depends(get_current_user)):
    task = sync_user_inbox.delay(str(user.id))
    return SyncTriggerResponse(task_id=task.id, status="queued")


@router.get("/sync/status/{task_id}")
async def sync_status(task_id: str, user: User = Depends(get_current_user)):
    """
    Frontend polls this instead of guessing with a fixed timeout. Returns
    Celery's task state plus whatever progress metadata the task reported
    (see sync_tasks.py `task.update_state` calls).
    """
    result = AsyncResult(task_id, app=celery_app)
    payload: dict = {"task_id": task_id, "state": result.state}

    if result.state == "PROGRESS":
        payload["meta"] = result.info
    elif result.state == "SUCCESS":
        payload["result"] = result.result
    elif result.state == "FAILURE":
        payload["error"] = str(result.info)

    return payload


@router.get("", response_model=list[EmailListItem])
async def list_emails(
    priority: Priority | None = None,
    category: EmailCategory | None = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = EmailRepository(db)
    messages = await repo.list_for_user(user.id, priority=priority, category=category, limit=limit, offset=offset)
    return [
        EmailListItem(
            id=m.id,
            sender=m.sender,
            subject=m.subject,
            snippet=m.snippet,
            received_at=m.received_at,
            priority=m.priority.value if m.priority else None,
            category=m.category.value if m.category else None,
            importance_score=m.importance_score,
            ai_summary_short=m.ai_summary_short,
            is_phishing_suspected=m.is_phishing_suspected,
        )
        for m in messages
    ]


@router.get("/{message_id}", response_model=EmailDetail)
async def get_email(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = EmailRepository(db)
    message = await repo.get(message_id)
    if message is None or message.user_id != user.id:
        raise HTTPException(status_code=404, detail="Email not found")

    return EmailDetail(
        id=message.id,
        sender=message.sender,
        subject=message.subject,
        snippet=message.snippet,
        received_at=message.received_at,
        priority=message.priority.value if message.priority else None,
        category=message.category.value if message.category else None,
        importance_score=message.importance_score,
        ai_summary_short=message.ai_summary_short,
        is_phishing_suspected=message.is_phishing_suspected,
        body_text=message.body_text,
        ai_summary_detailed=message.ai_summary_detailed,
        ai_summary_bullets=json.loads(message.ai_summary_bullets) if message.ai_summary_bullets else None,
        priority_reason=message.priority_reason,
        phishing_reason=message.phishing_reason,
        importance_positive_signals=json.loads(message.importance_positive_signals) if message.importance_positive_signals else None,
        importance_negative_signals=json.loads(message.importance_negative_signals) if message.importance_negative_signals else None,
    )


@router.post("/{message_id}/smart-replies", response_model=SmartReplyResult)
async def get_smart_replies(
    message_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_dep),
):
    repo = EmailRepository(db)
    message = await repo.get(message_id)
    if message is None or message.user_id != user.id:
        raise HTTPException(status_code=404, detail="Email not found")

    user_repo = UserRepository(db)
    preference = await user_repo.get_writing_preference(user.id)

    # Pull the rest of the thread for context -- a reply informed only by
    # the latest message misses things like "they already answered this in
    # message 2." Capped at the 5 most recent prior messages so the prompt
    # doesn't balloon on long threads.
    thread = await repo.get_thread_with_messages(message.thread_id)
    prior_messages = [m for m in thread.messages if m.id != message.id][-5:] if thread else []

    return await generate_smart_replies(
        llm,
        original_subject=message.subject,
        original_sender=message.sender,
        original_body=message.body_text,
        user_preferred_tone=preference.tone if preference else None,
        thread_history=[
            {"sender": m.sender, "body": m.body_text} for m in prior_messages
        ],
        importance_context=_importance_context(message),
    )


def _importance_context(message) -> str | None:
    """Turns the AI-derived signals already sitting on the message into a
    short context string so reply generation is informed by what the app
    already knows about this email, instead of re-deriving urgency from
    scratch with less information than the analysis pipeline had."""
    parts = []
    if message.priority:
        parts.append(f"urgency: {message.priority.value}")
    if message.category:
        parts.append(f"category: {message.category.value}")
    if message.importance_score is not None:
        parts.append(f"importance: {message.importance_score}/100")
    return ", ".join(parts) if parts else None


@router.post("/tone-check", response_model=ToneAnalysisResult)
async def check_tone(
    request: ToneAnalysisRequest,
    user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm_dep),
):
    """Runs before an outgoing draft is sent -- Feature 3, called from the compose UI."""
    return await analyze_tone(llm, draft_body=request.draft_body, recipient_context=request.recipient_context)


@router.post("/simplify")
async def simplify(
    request: SimplifyRequest,
    user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm_dep),
):
    simplified = await simplify_email(llm, original_body=request.body)
    return {"simplified": simplified}


@router.get("/threads/{thread_id}/summary")
async def get_thread_summary(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_dep),
):
    repo = EmailRepository(db)
    thread = await repo.get_thread_with_messages(thread_id)
    if thread is None or thread.messages[0].user_id != user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = [
        {"sender": m.sender, "sent_at": m.received_at.isoformat(), "body": m.body_text}
        for m in thread.messages
    ]
    return await summarize_thread(llm, messages=messages)
