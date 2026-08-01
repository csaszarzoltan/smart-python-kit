"""Standard API responses, bounded pagination, and stable error contracts."""
from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Select

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    data: DataT
    message: str = "Success"
    status: int = 200


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    total: int
    page: int = 1
    size: int = 20


class ErrorField(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: list[ErrorField] = []
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def create_response(data: Any, message: str = "Success", status: int = 200) -> APIResponse[Any]:
    return APIResponse(data=data, message=message, status=status)


def paginate(query: Select, page: int = 1, size: int = 20) -> tuple[Select, int, int]:
    """Validate pagination and apply SQL limit/offset."""
    if page < 1:
        raise ValueError("page must be at least 1")
    if not 1 <= size <= 100:
        raise ValueError("size must be between 1 and 100")
    return query.limit(size).offset((page - 1) * size), page, size


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid4())


def _error(status: int, code: str, message: str, request: Request, fields: list[dict[str, str]] | None = None) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "fields": fields or [], "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


async def _http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    codes = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found", 409: "conflict", 429: "rate_limited"}
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _error(exc.status_code, codes.get(exc.status_code, "http_error"), message, request)


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for issue in exc.errors():
        path = ".".join(str(part) for part in issue.get("loc", ()))
        fields.append({"field": path, "message": issue.get("msg", "Invalid value")})
    return _error(422, "validation_error", "One or more fields are invalid", request, fields)


async def _server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error(500, "internal_error", "Internal server error", request)


exception_handlers: dict[Any, Any] = {
    404: _http_error_handler,
    422: _validation_handler,
    500: _server_error_handler,
    HTTPException: _http_error_handler,
    RequestValidationError: _validation_handler,
    Exception: _server_error_handler,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type, handler in exception_handlers.items():
        if isinstance(exception_type, type):
            app.add_exception_handler(exception_type, handler)


__all__ = [
    "APIResponse", "ErrorDetail", "ErrorField", "ErrorResponse", "PaginatedResponse",
    "create_response", "exception_handlers", "paginate", "register_exception_handlers",
]
