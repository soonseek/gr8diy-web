"""Authentication service."""
import hmac
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserUpdate
from app.services.user import get_user_by_email

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate user with email and password.

    Uses constant-time comparison to prevent timing attacks that could
    be used to enumerate valid email addresses.
    """
    user = await get_user_by_email(db, email)

    if not user:
        # Use constant-time delay for non-existent users to prevent timing attacks
        verify_password(password, get_password_hash("dummy_hash_for_timing"))
        return None

    # Constant-time comparison for password verification
    if not verify_password(password, user.hashed_password):
        return None

    return user


async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Register a new user."""
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user registered: {user.email}")

    return user


async def create_tokens(user: User) -> Token:
    """Create access and refresh tokens for user."""
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"Tokens created for user: {user.email}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )
