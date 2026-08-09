import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.email_repository import ActionItemRepository
from app.schemas.api import ActionItemOut

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.get("", response_model=list[ActionItemOut])
async def list_action_items(
    include_completed: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ActionItemRepository(db)
    items = await repo.list_for_user(user.id, include_completed=include_completed)
    return items


@router.post("/{item_id}/complete", response_model=ActionItemOut)
async def complete_action_item(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ActionItemRepository(db)
    item = await repo.get(item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.is_completed = True
    await db.commit()
    return item
