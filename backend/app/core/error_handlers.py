import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("saveup.errors")


def _envelope(*, error_code: str, message: str, details: dict | None, request: Request) -> dict:
    """Builds the standard error envelope and makes it JSON-safe.

    ``details`` can legitimately contain values ``json.dumps`` cannot
    handle on its own -- most notably Pydantic v2's ``exc.errors()`` for
    a ``RequestValidationError``, which embeds a raw ``Decimal`` in
    ``input`` for numeric constraint failures (e.g. ``target_amount``'s
    ``gt=0``) and a raw ``ValueError`` instance in ``ctx.error`` for any
    ``@field_validator`` that raises one (e.g. phone number / lock_type
    checks). ``JSONResponse.render()`` uses the plain stdlib ``json``
    module with no custom encoder, so passing those straight through
    raises *inside this handler* -- which looks exactly like the
    original exception "escaping" unhandled. Routing the whole envelope
    through ``jsonable_encoder`` (the same helper FastAPI's own default
    validation-error handler uses) converts Decimals, UUIDs, datetimes,
    enums, and anything else json can't natively serialize, without
    changing the shape of already-serializable content.
    """
    request_id = getattr(request.state, "request_id", None)
    envelope = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        },
        "request_id": request_id,
    }
    return jsonable_encoder(envelope)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Unhandled application error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                request=request,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": exc.errors()},
                request=request,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(
                error_code="HTTP_ERROR",
                message=str(exc.detail),
                details={},
                request=request,
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={},
                request=request,
            ),
        )
