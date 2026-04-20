"""Shared error envelope + FastAPI exception mapping.

All client-facing errors shaped as {"error": {"code": ..., "message": ..., "request_id": ...}}.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class HubError(Exception):
    """Hub-internal error with explicit error code."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        headers: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}
        super().__init__(message)


def _envelope(code: str, message: str, request_id: str | None = None) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id or ""}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HubError)
    async def _hub_error(request: Request, exc: HubError):
        rid = request.headers.get("X-Request-ID", "")
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, rid),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException):
        rid = request.headers.get("X-Request-ID", "")
        code = _code_for_status(exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, str(exc.detail), rid),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError):
        rid = request.headers.get("X-Request-ID", "")
        return JSONResponse(
            status_code=422,
            content=_envelope("VALIDATION_ERROR", str(exc.errors()), rid),
        )


def _code_for_status(status: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "UPSTREAM_ERROR",
        503: "UNAVAILABLE",
    }.get(status, "ERROR")
