"""
Generic repository base.

Why the repository pattern here: services (business logic) should not
write raw SQLAlchemy queries inline — that couples business rules to
persistence details and makes services hard to unit test. Repositories own
all querying; services call repositories with domain-meaningful method
names (`get_unanalyzed_messages`, not `select(...).where(...)`).

This generic base handles the CRUD boilerplate; feature-specific
repositories subclass it and add domain queries.
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session = session
        self.model = model

    async def get(self, id: uuid.UUID) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def list_all(self) -> list[ModelType]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())
