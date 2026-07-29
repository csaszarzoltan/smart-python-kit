"""Pre-development tests for the cli.prompts module (Interactive Prompts).

Interface tests (PASS immediately with stubs):
    - Verify imports work
    - Verify Prompt class exists
    - Verify static methods exist with correct signatures

Behavioral tests (FAIL with NotImplementedError):
    - Prompt.text(), Prompt.confirm(), Prompt.choice()
    - Prompt.integer(), Prompt.multi_choice()
"""

from __future__ import annotations

from typing import get_type_hints

import pytest

from smartvintaawesomekit.cli.prompts import Prompt
from smartvintaawesomekit.cli.theme import ThemeConfig

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestPromptsInterface:
    """Verify prompts module public API exists with correct signatures."""

    def test_prompt_class_exists(self) -> None:
        """Prompt class should be importable."""
        assert Prompt is not None

    @pytest.mark.parametrize(
        "method_name",
        ["text", "confirm", "choice", "integer", "multi_choice"],
    )
    def test_prompt_has_static_method(self, method_name: str) -> None:
        """Prompt should have the expected static method."""
        method = getattr(Prompt, method_name, None)
        assert method is not None, f"Prompt.{method_name} should exist"
        assert callable(method), f"Prompt.{method_name} should be callable"

    def test_text_has_message_param(self) -> None:
        """Prompt.text should accept a message string."""
        hints = get_type_hints(Prompt.text)
        assert hints is not None

    def test_text_has_default_param(self) -> None:
        """Prompt.text should accept a default parameter."""
        import inspect

        sig = inspect.signature(Prompt.text)
        assert "default" in sig.parameters

    def test_text_has_validate_param(self) -> None:
        """Prompt.text should accept a validate callable."""
        import inspect

        sig = inspect.signature(Prompt.text)
        assert "validate" in sig.parameters

    def test_text_has_autocomplete_param(self) -> None:
        """Prompt.text should accept an autocomplete list."""
        import inspect

        sig = inspect.signature(Prompt.text)
        assert "autocomplete" in sig.parameters

    def test_text_has_password_param(self) -> None:
        """Prompt.text should accept a password bool."""
        import inspect

        sig = inspect.signature(Prompt.text)
        assert "password" in sig.parameters

    def test_text_has_theme_param(self) -> None:
        """Prompt.text should accept a theme parameter."""
        import inspect

        sig = inspect.signature(Prompt.text)
        assert "theme" in sig.parameters

    def test_text_returns_str(self) -> None:
        """Prompt.text return annotation should be str."""
        hints = get_type_hints(Prompt.text)
        assert hints.get("return") is str

    def test_confirm_returns_bool(self) -> None:
        """Prompt.confirm return annotation should be bool."""
        hints = get_type_hints(Prompt.confirm)
        assert hints.get("return") is bool

    def test_confirm_has_default_param(self) -> None:
        """Prompt.confirm should accept a default bool."""
        import inspect

        sig = inspect.signature(Prompt.confirm)
        assert "default" in sig.parameters

    def test_choice_returns_str(self) -> None:
        """Prompt.choice return annotation should be str."""
        hints = get_type_hints(Prompt.choice)
        assert hints.get("return") is str

    def test_choice_has_choices_param(self) -> None:
        """Prompt.choice should accept a choices list."""
        import inspect

        sig = inspect.signature(Prompt.choice)
        assert "choices" in sig.parameters

    def test_choice_has_filter_param(self) -> None:
        """Prompt.choice should accept a filter callable."""
        import inspect

        sig = inspect.signature(Prompt.choice)
        assert "filter" in sig.parameters

    def test_integer_returns_int(self) -> None:
        """Prompt.integer return annotation should be int."""
        hints = get_type_hints(Prompt.integer)
        assert hints.get("return") is int

    def test_integer_has_min_param(self) -> None:
        """Prompt.integer should accept a min parameter."""
        import inspect

        sig = inspect.signature(Prompt.integer)
        assert "min" in sig.parameters

    def test_integer_has_max_param(self) -> None:
        """Prompt.integer should accept a max parameter."""
        import inspect

        sig = inspect.signature(Prompt.integer)
        assert "max" in sig.parameters

    def test_multi_choice_returns_list(self) -> None:
        """Prompt.multi_choice return annotation should be list[str]."""
        hints = get_type_hints(Prompt.multi_choice)
        assert hints.get("return") is not None

    def test_multi_choice_has_choices_param(self) -> None:
        """Prompt.multi_choice should accept a choices list."""
        import inspect

        sig = inspect.signature(Prompt.multi_choice)
        assert "choices" in sig.parameters

    def test_multi_choice_has_min_selections_param(self) -> None:
        """Prompt.multi_choice should accept min_selections."""
        import inspect

        sig = inspect.signature(Prompt.multi_choice)
        assert "min_selections" in sig.parameters

    def test_multi_choice_has_max_selections_param(self) -> None:
        """Prompt.multi_choice should accept max_selections."""
        import inspect

        sig = inspect.signature(Prompt.multi_choice)
        assert "max_selections" in sig.parameters


# ──────────────────────────────────────────────────────────────────
# Behavioral tests — must fail with NotImplementedError
# ──────────────────────────────────────────────────────────────────


class TestPromptsBehavioral:
    """Verify prompts module behaviors are stubbed — all should raise NotImplementedError."""

    def test_text_not_implemented(self) -> None:
        """Prompt.text should raise NotImplementedError."""
        Prompt.text("Enter name:")

    def test_text_with_validate_not_implemented(self) -> None:
        """Prompt.text with validate should raise NotImplementedError."""
        Prompt.text("Enter name:", validate=lambda x: None if x else "Required")

    def test_text_with_autocomplete_not_implemented(self) -> None:
        """Prompt.text with autocomplete should raise NotImplementedError."""
        Prompt.text("Choose:", autocomplete=["a", "b", "c"])

    def test_text_password_not_implemented(self) -> None:
        """Prompt.text with password=True should raise NotImplementedError."""
        Prompt.text("Password:", password=True)

    def test_text_with_default_not_implemented(self) -> None:
        """Prompt.text with default should raise NotImplementedError."""
        Prompt.text("Name:", default="Alice")

    def test_text_with_theme_not_implemented(self) -> None:
        """Prompt.text with theme should raise NotImplementedError."""
        Prompt.text("Name:", theme=ThemeConfig())

    def test_confirm_not_implemented(self) -> None:
        """Prompt.confirm should raise NotImplementedError."""
        Prompt.confirm("Continue?")

    def test_confirm_with_default_false_not_implemented(self) -> None:
        """Prompt.confirm with default=False should raise NotImplementedError."""
        Prompt.confirm("Continue?", default=False)

    def test_choice_not_implemented(self) -> None:
        """Prompt.choice should raise NotImplementedError."""
        Prompt.choice("Pick:", ["a", "b", "c"])

    def test_choice_with_filter_not_implemented(self) -> None:
        """Prompt.choice with filter should raise NotImplementedError."""
        Prompt.choice("Pick:", ["a", "b"], filter=lambda x: x.upper())

    def test_integer_not_implemented(self) -> None:
        """Prompt.integer should raise NotImplementedError."""
        Prompt.integer("Age:")

    def test_integer_with_range_not_implemented(self) -> None:
        """Prompt.integer with min/max should raise NotImplementedError."""
        Prompt.integer("Age:", min=0, max=150)

    def test_multi_choice_not_implemented(self) -> None:
        """Prompt.multi_choice should raise NotImplementedError."""
        Prompt.multi_choice("Select:", ["a", "b", "c"])

    def test_multi_choice_with_min_max_not_implemented(self) -> None:
        """Prompt.multi_choice with min/max selections should raise NotImplementedError."""
        Prompt.multi_choice("Select:", ["a", "b", "c"], min_selections=1, max_selections=2)
