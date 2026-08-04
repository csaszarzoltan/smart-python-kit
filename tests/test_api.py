"""Behavioral and interface tests for the api module.

Interface tests:
    - Verify imports work
    - Verify Pydantic models exist with correct fields
    - Verify function signatures and type hints

Behavioral tests:
    - create_response() raises
    - paginate() raises
    - register_exception_handlers() raises
"""

from __future__ import annotations

from typing import get_type_hints

from smartvintaawesomekit.api import (
    APIResponse,
    PaginatedResponse,
    create_response,
    exception_handlers,
    paginate,
    register_exception_handlers,
)

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────

class TestApiInterface:
    """Verify api module public API exists with correct signatures."""

    def test_apiresponse_class_exists(self) -> None:
        """APIResponse class should be importable."""
        assert APIResponse is not None

    def test_paginatedresponse_class_exists(self) -> None:
        """PaginatedResponse class should be importable."""
        assert PaginatedResponse is not None

    def test_create_response_function_exists(self) -> None:
        """create_response function should be importable."""
        assert create_response is not None

    def test_paginate_function_exists(self) -> None:
        """paginate function should be importable."""
        assert paginate is not None

    def test_exception_handlers_exists(self) -> None:
        """exception_handlers dict should be importable."""
        assert exception_handlers is not None

    def test_register_exception_handlers_exists(self) -> None:
        """register_exception_handlers function should be importable."""
        assert register_exception_handlers is not None

    def test_apiresponse_is_pydantic_model(self) -> None:
        """APIResponse should be a Pydantic BaseModel."""
        from pydantic import BaseModel
        assert issubclass(APIResponse, BaseModel)

    def test_paginatedresponse_is_pydantic_model(self) -> None:
        """PaginatedResponse should be a Pydantic BaseModel."""
        from pydantic import BaseModel
        assert issubclass(PaginatedResponse, BaseModel)

    def test_apiresponse_is_generic(self) -> None:
        """APIResponse should be a generic model."""
        is_generic = hasattr(APIResponse, "__class_getitem__")
        has_orig = hasattr(APIResponse, "__orig_bases__")
        assert is_generic or has_orig

    def test_paginatedresponse_is_generic(self) -> None:
        """PaginatedResponse should be a generic model."""
        is_generic = hasattr(PaginatedResponse, "__class_getitem__")
        has_orig = hasattr(PaginatedResponse, "__orig_bases__")
        assert is_generic or has_orig

    def test_apiresponse_has_data_field(self) -> None:
        """APIResponse should have a data field."""
        assert "data" in APIResponse.model_fields

    def test_apiresponse_has_message_field(self) -> None:
        """APIResponse should have a message field."""
        assert "message" in APIResponse.model_fields

    def test_apiresponse_has_status_field(self) -> None:
        """APIResponse should have a status field."""
        assert "status" in APIResponse.model_fields

    def test_paginatedresponse_has_items_field(self) -> None:
        """PaginatedResponse should have an items field."""
        assert "items" in PaginatedResponse.model_fields

    def test_paginatedresponse_has_total_field(self) -> None:
        """PaginatedResponse should have a total field."""
        assert "total" in PaginatedResponse.model_fields

    def test_paginatedresponse_has_page_field(self) -> None:
        """PaginatedResponse should have a page field."""
        assert "page" in PaginatedResponse.model_fields

    def test_paginatedresponse_has_size_field(self) -> None:
        """PaginatedResponse should have a size field."""
        assert "size" in PaginatedResponse.model_fields

    def test_create_response_signature(self) -> None:
        """create_response should accept data, message, and status."""
        import inspect
        sig = inspect.signature(create_response)
        param_names = list(sig.parameters.keys())
        assert "data" in param_names
        assert "message" in param_names
        assert "status" in param_names

    def test_paginate_signature(self) -> None:
        """paginate should accept query, page, and size."""
        import inspect
        sig = inspect.signature(paginate)
        param_names = list(sig.parameters.keys())
        assert "query" in param_names
        assert "page" in param_names
        assert "size" in param_names

    def test_register_exception_handlers_signature(self) -> None:
        """register_exception_handlers should accept an app parameter."""
        import inspect
        sig = inspect.signature(register_exception_handlers)
        param_names = list(sig.parameters.keys())
        assert "app" in param_names

    def test_create_response_returns_apiresponse(self) -> None:
        """create_response should return APIResponse."""
        hints = get_type_hints(create_response)
        assert "return" in hints

    def test_paginate_returns_tuple(self) -> None:
        """paginate should return a tuple."""
        hints = get_type_hints(paginate)
        assert "return" in hints

    def test_exception_handlers_is_dict(self) -> None:
        """exception_handlers should be a dict."""
        assert isinstance(exception_handlers, dict)

    def test_exception_handlers_has_404(self) -> None:
        """exception_handlers should contain 404 handler."""
        assert 404 in exception_handlers

    def test_exception_handlers_has_422(self) -> None:
        """exception_handlers should contain 422 handler."""
        assert 422 in exception_handlers

    def test_exception_handlers_has_500(self) -> None:
        """exception_handlers should contain 500 handler."""
        assert 500 in exception_handlers

    def test_all_exports_listed(self) -> None:
        """Verify __all__ exports match expected public API."""
        from smartvintaawesomekit import api
        exports = api.__all__
        assert "APIResponse" in exports
        assert "PaginatedResponse" in exports
        assert "create_response" in exports
        assert "paginate" in exports
        assert "exception_handlers" in exports
        assert "register_exception_handlers" in exports


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# These call stubs as if implemented; NotImplementedError propagates as test FAILURE.
# ──────────────────────────────────────────────────────────────────

class TestApiBehavioral:
    """Verify api module behaviors are stubbed — all should raise NotImplementedError."""

    def test_create_response_not_implemented(self) -> None:
        """create_response should raise NotImplementedError."""
        create_response(data={"key": "value"})

    def test_paginate_not_implemented(self) -> None:
        """paginate should raise NotImplementedError."""
        from sqlalchemy import select
        query = select(1)
        paginate(query=query)

    def test_register_exception_handlers_not_implemented(self) -> None:
        """register_exception_handlers should raise NotImplementedError."""
        from fastapi import FastAPI
        app = FastAPI()
        register_exception_handlers(app=app)
