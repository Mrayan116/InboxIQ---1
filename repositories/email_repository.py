import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.email import ActionItem, EmailCategory, EmailMessage, EmailThread, Priority
from app.repositories.base import BaseRepository


class EmailRepository(BaseRepository[EmailMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EmailMessage)

    async def get_by_gmail_id(self, gmail_message_id: str) -> EmailMessage | None:
        result = await self.session.execute(
            select(EmailMessage).where(EmailMessage.gmail_message_id == gmail_message_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        priority: Priority | None = None,
        category: EmailCategory | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmailMessage]:
        query = select(EmailMessage).where(EmailMessage.user_id == user_id)
        if priority:
            query = query.where(EmailMessage.priority == priority)
        if category:
            query = query.where(EmailMessage.category == category)
        query = query.order_by(EmailMessage.received_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unanalyzed(self, user_id: uuid.UUID, limit: int = 20) -> list[EmailMessage]:
        """Emails synced from Gmail but not yet run through the AI pipeline."""
        query = (
            select(EmailMessage)
            .where(EmailMessage.user_id == user_id, EmailMessage.analyzed_at.is_(None))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_thread_with_messages(self, thread_id: uuid.UUID) -> EmailThread | None:
        query = (
            select(EmailThread)
            .where(EmailThread.id == thread_id)
            .options(selectinload(EmailThread.messages))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_thread(self, user_id: uuid.UUID, gmail_thread_id: str, subject: str) -> EmailThread:
        result = await self.session.execute(
            select(EmailThread).where(
                EmailThread.user_id == user_id, EmailThread.gmail_thread_id == gmail_thread_id
            )
        )
        thread = result.scalar_one_or_none()
        if thread is None:
            thread = EmailThread(user_id=user_id, gmail_thread_id=gmail_thread_id, subject=subject)
            self.session.add(thread)
            await self.session.flush()
        return thread


class ActionItemRepository(BaseRepository[ActionItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ActionItem)

    async def list_for_user(self, user_id: uuid.UUID, *, include_completed: bool = False) -> list[ActionItem]:
        query = select(ActionItem).where(ActionItem.user_id == user_id)
        if not include_completed:
            query = query.where(ActionItem.is_completed.is_(False))
        query = query.order_by(ActionItem.due_date.asc().nulls_last())
        result = await self.session.execute(query)
        return list(result.scalars().all())
