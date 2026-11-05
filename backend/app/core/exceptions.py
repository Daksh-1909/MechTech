import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_request_id

logger = logging.getLogger(__name__)

_HTTP_ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "NOT_READY",
}


class AppError(Exception):
    def __init__(
        self,
        message: str = "Request could not be processed.",
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or get_request_id()


def _error_body(
    request: Request,
    *,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": _request_id(request),
    }
    if details:
        error["details"] = details
    return {"error": error}


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ()) if str(part) not in {"body"}]
        details.append(
            {
                "field": ".".join(location) or "(request)",
                "issue": str(error.get("msg", "Invalid value.")),
            }
        )
    return details


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("Application error: %s", exc.code, exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            request,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_body(
            request,
            code="VALIDATION_ERROR",
            message="The submitted request is invalid.",
            details=_validation_details(exc),
        ),
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    if exc.status_code >= 500:
        message = "The service is temporarily unavailable."
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = "Request could not be processed."

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(request, code=code, message=message),
        headers=getattr(exc, "headers", None),
    )


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing request")
    return JSONResponse(
        status_code=500,
        content=_error_body(
            request,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
