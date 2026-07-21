"""Domain exceptions + central handlers.

Services raise DOMAIN exceptions (no HTTP knowledge); one handler maps them to
consistent JSON errors. Adding a new error type = one class + one table row,
and every endpoint automatically behaves the same.
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = structlog.get_logger()


class DomainError(Exception):
    """Base for expected, business-level failures."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class AuthenticationError(DomainError):
    status_code = 401
    code = "unauthorized"


class RateLimitError(DomainError):
    status_code = 429
    code = "rate_limited"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        log.info("domain_error", code=exc.code, path=request.url.path, detail=exc.message)
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Unexpected = bug. Log with traceback, return NO internal details (no
        # stack traces or SQL to attackers).
        log.error("unhandled_exception", path=request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Internal server error"}},
        )
