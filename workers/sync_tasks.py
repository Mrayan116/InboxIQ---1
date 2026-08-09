"""
Background tasks: fetch new Gmail messages, persist them, run AI analysis.

Two distinct bugs were fixed here (see git history if you're tracking one):

1. Sequential-only processing -- 25 emails processed one at a time, each
   waiting for the previous email's full AI pipeline to finish, made sync
   feel slow. Fixed by fetching Gmail messages concurrently and analyzing
   newly-inserted messages concurrently, each analysis task owning its own
   AsyncSession (never shared across concurrent coroutines).

2. Cross-event-loop connection reuse -- `engine` in app/core/database.py is
   a module-level singleton created once at import time. asyncpg
   connections are bound to the event loop that created them. Celery runs
   each task via `asyncio.run(...)`, which creates a NEW event loop per
   task and destroys it when the task finishes. If the engine's pooled
   connections survive past that loop's closure, the next task's new loop
   gets handed a connection whose internal state belongs to a dead loop --
   asyncpg raises "cannot perform operation: another operation is in
   progress" because the connection's operation state is corrupted across
   the loop boundary. This can happen even with fully sequential code and
   even on a SECOND sync click, not just under concurrency.
   Fixed by disposing the engine's connection pool at the end of every task
   invocation, forcing a clean pool (and fresh connections, bound to
   whatever loop asyncio.run() creates next) on the next run.
"""

import asyncio
import uuid

from app.core.database import AsyncSessionLocal, engine
from app.core.logging import get_logger
from app.llm.factory import get_llm_provider
from app.models.email import EmailMessage
from app.models.user import User
from app.repositories.email_repository import EmailRepository
from app.repositories.user_repository import UserRepository
from app.services.ai.analysis_pipeline import analyze_email
from app.services.gmail_service import GmailService
from app.workers.celery_app import celery_app

logger = get_logger(__name__)

# Caps concurrent LLM analysis calls. Groq's free tier has a requests/min
# ceiling -- 5 emails in flight at once (each firing 5 concurrent AI calls
# internally) is a reasonable balance of speed vs not tripping rate limits.
ANALYSIS_CONCURRENCY = 5

# Caps concurrent Gmail API fetches during the insert phase.
FETCH_CONCURRENCY = 8


async def _fetch_and_insert_new_messages(
    session, user_id: uuid.UUID, gmail: GmailService, email_repo: EmailRepository
) -> list[uuid.UUID]:
    """
    Fetches from Gmail concurrently (network-bound, no DB involved), then
    inserts SEQUENTIALLY using the one session passed in. The insert loop
    is a plain `for`, not `asyncio.gather` -- multiple coroutines must
    never `await` on the same AsyncSession concurrently, so writes here
    are deliberately serialized even though fetching above is not.
    """
    message_ids = gmail.list_recent_message_ids(max_results=25)

    to_fetch = [
        gmail_id for gmail_id in message_ids
        if await email_repo.get_by_gmail_id(gmail_id) is None
    ]
    if not to_fetch:
        return []

    semaphore = asyncio.Semaphore(FETCH_CONCURRENCY)

    async def fetch_one(gmail_id: str) -> dict:
        async with semaphore:
            # gmail.get_message is a synchronous (blocking) HTTP call under
            # the hood; run it in a thread so it doesn't block the event
            # loop or serialize against the other fetches. No DB access
            # happens in this function, so this gather is safe.
            return await asyncio.to_thread(gmail.get_message, gmail_id)

    fetched = await asyncio.gather(*[fetch_one(gid) for gid in to_fetch], return_exceptions=True)

    new_ids: list[uuid.UUID] = []
    for gmail_id, data in zip(to_fetch, fetched):
        if isinstance(data, BaseException):
            logger.error("Failed to fetch Gmail message %s: %s", gmail_id, data)
            continue

        # Sequential DB writes on the single shared session -- safe because
        # there is no concurrency here, just a for-loop over already-fetched data.
        thread = await email_repo.get_or_create_thread(
            user_id, data["gmail_thread_id"], data["subject"]
        )
        message = EmailMessage(
            thread_id=thread.id,
            user_id=user_id,
            gmail_message_id=data["gmail_message_id"],
            sender=data["sender"],
            sender_domain=data["sender_domain"],
            subject=data["subject"],
            snippet=data["snippet"],
            body_text=data["body_text"],
            received_at=data["received_at"],
        )
        await email_repo.create(message)
        new_ids.append(message.id)

    await session.commit()
    return new_ids


async def _analyze_one(message_id: uuid.UUID, semaphore: asyncio.Semaphore) -> None:
    """
    Owns its entire DB lifecycle: opens a fresh AsyncSession, loads the
    message, runs analysis, commits, closes. This function is designed to
    run as one of many concurrent tasks in asyncio.gather() -- it NEVER
    touches a session created outside itself, so there is nothing for two
    concurrent invocations to contend over.
    """
    async with semaphore:
        async with AsyncSessionLocal() as session:
            message = await session.get(EmailMessage, message_id)
            if message is None:
                return
            llm = get_llm_provider()
            try:
                await analyze_email(session, llm, message)
            except Exception:
                logger.exception("AI analysis failed for message %s", message_id)


async def _sync_and_analyze(user_id: uuid.UUID, task=None) -> dict:
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user: User | None = await user_repo.get(user_id)
        if user is None:
            return {"error": "user not found"}

        gmail_account = await user_repo.get_gmail_account(user_id)
        if gmail_account is None:
            return {"error": "no connected Gmail account"}

        gmail = GmailService(gmail_account)
        email_repo = EmailRepository(session)

        if task:
            task.update_state(state="PROGRESS", meta={"phase": "fetching"})
        new_ids = await _fetch_and_insert_new_messages(session, user_id, gmail, email_repo)

        if not new_ids:
            return {"new_messages": 0}

        if task:
            task.update_state(state="PROGRESS", meta={"phase": "analyzing", "total": len(new_ids)})

        # Each _analyze_one call opens and closes its OWN session -- this
        # gather() has zero shared mutable DB state across its coroutines.
        semaphore = asyncio.Semaphore(ANALYSIS_CONCURRENCY)
        await asyncio.gather(*[_analyze_one(mid, semaphore) for mid in new_ids])

        return {"new_messages": len(new_ids)}


@celery_app.task(name="sync_user_inbox", bind=True)
def sync_user_inbox(self, user_id: str) -> dict:
    async def run() -> dict:
        try:
            return await _sync_and_analyze(uuid.UUID(user_id), task=self)
        finally:
            # Critical: dispose the connection pool before this event loop
            # closes. Without this, the next `asyncio.run()` call (next
            # task, or the next click of "Sync") gets a new loop but a pool
            # still holding connections bound to THIS loop, which is the
            # direct cause of asyncpg's "another operation is in progress".
            await engine.dispose()

    return asyncio.run(run())
