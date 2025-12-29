"""Authentication endpoints."""
import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.deps import get_db
from app.schemas.user import LoginRequest, RefreshTokenRequest, Token, UserCreate, User
from app.services.auth import authenticate_user, create_tokens, register_user

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check if user already exists
    from app.services.user import get_user_by_email

    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await register_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_in: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns access_token in response body and sets refresh_token as httpOnly cookie.
    """
    user = await authenticate_user(db, login_in.email, login_in.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {login_in.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    tokens = await create_tokens(user)

    # Set refresh_token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # Only send over HTTPS in production
        samesite="lax",
        max_age=int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()),
        path="/",
    )

    logger.info(f"User logged in: {user.email}")

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_in: RefreshTokenRequest | None = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    Refresh access token using refresh token.

    Refresh token can be provided in request body or as httpOnly cookie.
    """
    from app.core.security import verify_token
    from app.services.user import get_user_by_id

    # Get refresh token from cookie or request body
    refresh_token = None
    if request:
        refresh_token = request.cookies.get("refresh_token")

    if refresh_in and refresh_in.refresh_token:
        refresh_token = refresh_in.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    payload = verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    # Fixed: user_id is string UUID, don't cast to int
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    tokens = await create_tokens(user)

    # Update refresh_token cookie
    if response:
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.ENVIRONMENT == "production",
            samesite="lax",
            max_age=int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()),
            path="/",
        )

    logger.info(f"Token refreshed for user: {user.email}")

    return tokens


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing refresh_token cookie.

    Note: In a production system, you should also invalidate the token
    in Redis or a token blacklist.
    """
    response.delete_cookie(
        key="refresh_token",
        path="/",
    )

    return {"message": "Successfully logged out"}
