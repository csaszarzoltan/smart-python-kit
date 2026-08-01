"""Smart API utilities — standardized response formats, pagination, and error handling.

Provides generic API response wrappers, SQLAlchemy query pagination,
and ready-to-register FastAPI exception handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Select  # noqa: TC002

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper.

    Attributes:
        data: The response payload.
        message: A human-readable message.
        status: HTTP status code.
    """

    data: DataT
    message: str = "Success"
    status: int = 200


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standard paginated API response.

    Attributes:
        items: The list of items for the current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        size: Number of items per page.
    """

    items: list[DataT]
    total: int
    page: int = 1
    size: int = 20


def create_response(
    data: Any,  # noqa: ANN401
    message: str = "Success",
    status: int = 200,
) -> APIResponse[Any]:
    """Create a standardized API response.

    Args:
        data: The response payload.
        message: A human-readable message.
        status: HTTP status code.

    Returns:
        An APIResponse instance wrapping the data.
    """
    return APIResponse(data=data, message=message, status=status)


def paginate(
    query: Select,
    page: int = 1,
    size: int = 20,
) -> tuple[Select, int, int]:
    """Apply pagination to a SQLAlchemy select query.

    Returns the query unchanged along with page/size metadata.
    The caller applies offset/limit when executing.

    Args:
        query: A SQLAlchemy Select statement.
        page: Page number (1-indexed).
        size: Items per page.

    Returns:
        A tuple of (paginated_select, page, size) for use with offset/limit.
    """
    if page < 1:
        raise ValueError("page must be at least 1")
    if not 1 <= size <= 100:
        raise ValueError("size must be between 1 and 100")
    return query.limit(size).offset((page - 1) * size), page, size


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 404 Not Found exceptions."""
    return JSONResponse(
        status_code=404,
        content={"data": None, "message": "Resource not found", "status": 404},
    )


def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 422 Validation Error exceptions."""
    return JSONResponse(
        status_code=422,
        content={"data": None, "message": "Validation error", "status": 422},
    )


def _server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 Internal Server Error exceptions."""
    return JSONResponse(
        status_code=500,
        content={"data": None, "message": "Internal server error", "status": 500},
    )


exception_handlers: dict[int | type[Exception], Any] = {
    404: _not_found_handler,
    422: _validation_handler,
    500: _server_error_handler,
}
"""Exception handlers dict ready to be registered on a FastAPI app.

Usage:
    app = FastAPI()
    for exc, handler in exception_handlers.items():
        app.add_exception_handler(exc, handler)
"""


def register_exception_handlers(app: FastAPI) -> None:
    """Register all standard exception handlers on a FastAPI app.

    Args:
        app: A FastAPI application instance.
    """
    for status_code, handler in exception_handlers.items():
        app.add_exception_handler(status_code, handler)


__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "create_response",
    "paginate",
    "exception_handlers",
    "register_exception_handlers",
]
