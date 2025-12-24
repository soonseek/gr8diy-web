"""Rate limiting middleware using Redis."""
import logging
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitError
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for API endpoints."""

    def __init__(self, app, redis_client, default_limit: int = 100, window: int = 60):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            redis_client: Redis client instance
            default_limit: Max requests per window (default: 100)
            window: Time window in seconds (default: 60)
        """
        super().__init__(app)
        self.redis = redis_client
        self.default_limit = default_limit
        self.window = window

        # Rate limits for specific endpoints
        self.endpoint_limits = {
            "/api/v1/auth/login": (5, 60),  # 5 requests per minute
            "/api/v1/auth/register": (3, 300),  # 3 requests per 5 minutes
            "/api/v1/auth/refresh": (10, 60),  # 10 requests per minute
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply rate limiting."""
        # Skip rate limiting in development mode
        if settings.ENVIRONMENT == "development":
            return await call_next(request)

        # Get client identifier (IP address or user ID if authenticated)
        client_id = await self._get_client_id(request)

        # Get rate limit for this endpoint
        path = request.url.path
        limit, window = self.endpoint_limits.get(path, (self.default_limit, self.window))

        # Check rate limit
        try:
            allowed, retry_after = await self._check_rate_limit(client_id, path, limit, window)

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for client {client_id} on {path}",
                    extra={"client_id": client_id, "path": path},
                )
                raise RateLimitError(
                    message="Rate limit exceeded. Please try again later.",
                    retry_after=retry_after,
                )

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(limit - 1)  # Simplified
            response.headers["X-RateLimit-Window"] = str(window)

            return response

        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            # Fail open - allow request if rate limiting fails
            return await call_next(request)

    async def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # For authenticated users, we'd decode the token
            # For now, use IP address
            pass

        # Use IP address as fallback
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(
        self, client_id: str, path: str, limit: int, window: int
    ) -> tuple[bool, int | None]:
        """
        Check if request is within rate limit.

        Returns:
            (allowed: bool, retry_after: int | None)
        """
        key = f"rate_limit:{client_id}:{path}"

        try:
            # Use Redis pipeline for atomic operation
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = await pipe.execute()

            current = results[0]

            if current > limit:
                ttl = await self.redis.ttl(key)
                return False, ttl

            return True, None

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open - allow request
            return True, None
