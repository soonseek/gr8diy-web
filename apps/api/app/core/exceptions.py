"""Global exception handlers for structured error responses."""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Validation error exception."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class AuthenticationError(APIError):
    """Authentication error exception."""

    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class NotFoundError(APIError):
    """Not found error exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class PermissionError(APIError):
    """Permission error exception."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class RateLimitError(APIError):
    """Rate limit exceeded exception."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int | None = None):
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, details)


def format_error_response(
    status_code: int,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Format standardized error response."""
    error_data: dict[str, Any] = {
        "error": {
            "message": message,
            "code": status_code,
        }
    }
    if details:
        error_data["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=error_data)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API exceptions."""
    logger.warning(
        f"API error: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "details": exc.details,
        },
    )
    return format_error_response(exc.status_code, exc.message, exc.details)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"Validation error: {len(errors)} error(s)",
        extra={"path": request.url.path, "errors": errors},
    )

    return format_error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Validation failed",
        {"errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    # Don't expose internal errors in production
    message = "An internal server error occurred"

    return format_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        message,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup all exception handlers for the application."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
