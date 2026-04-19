from __future__ import annotations

from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    CREDITS_DEPLETED = "CREDITS_DEPLETED"
    VM_WAKING = "VM_WAKING"
    VM_UNAVAILABLE = "VM_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    INTERNAL = "INTERNAL"


_STATUS: dict[ErrorCode, int] = {
    ErrorCode.AUTH_REQUIRED: 401,
    ErrorCode.AUTH_INVALID: 401,
    ErrorCode.CREDITS_DEPLETED: 402,
    ErrorCode.VM_WAKING: 503,
    ErrorCode.VM_UNAVAILABLE: 503,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION: 422,
    ErrorCode.INTERNAL: 500,
}


class ErrorShape(BaseModel):
    code: ErrorCode
    message: str
    detail: dict | None = None


class ArticError(Exception):
    code: ErrorCode = ErrorCode.INTERNAL

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    @property
    def status_code(self) -> int:
        return _STATUS[self.code]

    def to_shape(self) -> ErrorShape:
        return ErrorShape(code=self.code, message=self.message, detail=self.detail)


class AuthRequired(ArticError):
    code = ErrorCode.AUTH_REQUIRED


class AuthInvalid(ArticError):
    code = ErrorCode.AUTH_INVALID


class CreditsDepleted(ArticError):
    code = ErrorCode.CREDITS_DEPLETED


class VmWaking(ArticError):
    code = ErrorCode.VM_WAKING


class VmUnavailable(ArticError):
    code = ErrorCode.VM_UNAVAILABLE


class RateLimited(ArticError):
    code = ErrorCode.RATE_LIMITED


class NotFound(ArticError):
    code = ErrorCode.NOT_FOUND


class Validation(ArticError):
    code = ErrorCode.VALIDATION


class Internal(ArticError):
    code = ErrorCode.INTERNAL


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ArticError)
    async def _artic_handler(_: Request, exc: ArticError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_shape().model_dump(mode="json"))
