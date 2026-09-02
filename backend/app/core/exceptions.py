"""Domain-level exceptions.

Services raise these instead of HTTPException so that business logic
stays framework-agnostic and testable without spinning up FastAPI. The
handlers registered in ``app.core.error_handlers`` translate each of
these into a consistent JSON error envelope.
"""


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, error_code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
        self.details = details or {}


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class ValidationAppError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"


class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"


class RateLimitedError(AppError):
    status_code = 429
    error_code = "RATE_LIMITED"


class InsufficientBalanceError(ConflictError):
    error_code = "INSUFFICIENT_BALANCE"


class InvalidOTPError(AppError):
    status_code = 400
    error_code = "INVALID_OTP"


class OTPExpiredError(AppError):
    status_code = 400
    error_code = "OTP_EXPIRED"
