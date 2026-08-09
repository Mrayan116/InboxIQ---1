from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import GmailAccount, User, WritingPreference
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_gmail_account(self, user_id) -> GmailAccount | None:
        result = await self.session.execute(
            select(GmailAccount).where(GmailAccount.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_writing_preference(self, user_id) -> WritingPreference | None:
        """
        Explicit query, never `user.writing_preference`. AsyncSession does
        not support implicit lazy loading -- touching an unloaded
        relationship attribute on an object fetched from an async session
        raises MissingGreenlet, which crashes the request hard enough that
        the browser reports it as a raw network failure rather than a
        clean error response.
        """
        result = await self.session.execute(
            select(WritingPreference).where(WritingPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
