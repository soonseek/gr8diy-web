"""User schemas."""
from datetime import datetime
from typing import Any

import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.config import get_settings

settings = get_settings()


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
            )

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))

        errors = []
        if settings.PASSWORD_REQUIRE_UPPERCASE and not has_upper:
            errors.append("one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not has_lower:
            errors.append("one lowercase letter")
        if settings.PASSWORD_REQUIRE_DIGIT and not has_digit:
            errors.append("one digit")
        if settings.PASSWORD_REQUIRE_SPECIAL and not has_special:
            errors.append("one special character")

        if errors:
            raise ValueError(
                f"Password must contain {', '.join(errors)}. "
                f"Example: MySecureP@ssw0rd"
            )

        # Check for common passwords
        common_passwords = [
            "password", "12345678", "qwerty", "abc123", "password1",
            "welcome", "monkey", "dragon", "master", "hello"
        ]
        if v.lower() in common_passwords:
            raise ValueError("This password is too common. Please choose a stronger password.")

        return v


class UserUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str | None) -> str | None:
        """Validate password meets complexity requirements."""
        if v is None:
            return v

        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
            )

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', v))

        errors = []
        if settings.PASSWORD_REQUIRE_UPPERCASE and not has_upper:
            errors.append("one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not has_lower:
            errors.append("one lowercase letter")
        if settings.PASSWORD_REQUIRE_DIGIT and not has_digit:
            errors.append("one digit")
        if settings.PASSWORD_REQUIRE_SPECIAL and not has_special:
            errors.append("one special character")

        if errors:
            raise ValueError(
                f"Password must contain {', '.join(errors)}. "
                f"Example: MySecureP@ssw0rd"
            )

        return v


class UserInDB(UserBase):
    """User schema with ID and timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class User(UserInDB):
    """User schema returned to clients."""

    pass


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str | None = None
    exp: int | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
