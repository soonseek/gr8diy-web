"""User endpoints."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.v1.auth import router as auth_router
from app.core.deps import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user."""
    return current_user


@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get list of users."""
    from app.services.user import get_users

    users = await get_users(db, skip=skip, limit=limit)
    return users
