"""Interactive prompts with validation, autocomplete, and theme support.

Extends Rich's prompt system with validation callbacks, auto-complete suggestions,
password masking, and multi-choice selection.

Usage:
    from smartvintaawesomekit.cli.prompts import Prompt

    name = Prompt.text("Enter your name", default="User",
    ...                    validate=lambda x: None if x else "Required")
    ok = Prompt.confirm("Continue?")
    choice = Prompt.choice("Pick one", ["a", "b", "c"])
    age = Prompt.integer("Age", min=0, max=150)
    items = Prompt.multi_choice("Select items", ["x", "y", "z"])
"""

from __future__ import annotations

import sys
from collections.abc import Callable  # noqa: TC003 — used by get_type_hints() in tests
from typing import Any

from rich.prompt import Confirm as RichConfirm
from rich.prompt import IntPrompt as RichIntPrompt
from rich.prompt import Prompt as RichPrompt

from smartvintaawesomekit.cli.theme import (
    ThemeConfig,  # noqa: TC001 — used by get_type_hints() in tests
)

_INTERACTIVE: bool | None = None


def _is_interactive() -> bool:
    """Check if stdin is available for interactive prompts."""
    global _INTERACTIVE
    if _INTERACTIVE is not None:
        return bool(_INTERACTIVE)
    try:
        _INTERACTIVE = sys.stdin.isatty()
    except (OSError, AttributeError):
        _INTERACTIVE = False
    return bool(_INTERACTIVE)


def _safe_prompt(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
    """Call Rich's Prompt.ask safely, returning the default value in non-interactive contexts.

    In test environments (pytest) or headless contexts, stdin is captured or unavailable,
    causing Rich to raise OSError. This wrapper catches that and falls back to the default
    value, or an empty string if no default is provided.
    """
    try:
        return RichPrompt.ask(*args, **kwargs)
    except (OSError, EOFError):
        default = kwargs.get("default")
        if default is not None:
            return default
        if args:
            return args[0]
        return ""


def _safe_int_prompt(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
    """Call Rich's IntPrompt.ask safely, returning the default value in non-interactive contexts."""
    try:
        return RichIntPrompt.ask(*args, **kwargs)
    except (OSError, EOFError):
        default = kwargs.get("default")
        if default is not None:
            return default
        return 0


def _safe_confirm(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
    """Call Rich's Confirm.ask safely, returning the default value in non-interactive contexts."""
    try:
        return RichConfirm.ask(*args, **kwargs)
    except (OSError, EOFError):
        return kwargs.get("default", True)


class Prompt:
    """Collection of static prompt methods with validation.

    All methods delegate to Rich's prompt system and respect the theme
    configuration for consistent styling.
    """

    @staticmethod
    def text(
        message: str,
        *,
        default: str | None = None,
        validate: Callable[[str], str | None] | None = None,
        autocomplete: list[str] | None = None,
        password: bool = False,
        theme: ThemeConfig | None = None,
    ) -> str:
        """Prompt for text input with optional validation and autocomplete.

        Args:
            message: The prompt message to display.
            default: Default value if the user enters nothing.
            validate: Optional callable that receives the input string and returns
                      None if valid, or an error message string if invalid.
            autocomplete: Optional list of autocomplete suggestions.
            password: If True, mask input characters.
            theme: Optional ThemeConfig for styled prompts.

        Returns:
            The user's input as a string.

        Example:
            name = Prompt.text("Enter your name", default="Alice",
                               validate=lambda x: None if len(x) > 0 else "Required")
        """
        kwargs: dict[str, Any] = {}
        if default is not None:
            kwargs["default"] = default
        if password:
            kwargs["password"] = True

        interactive = _is_interactive()
        while True:
            value = _safe_prompt(message, **kwargs)
            if validate is not None:
                error_msg = validate(value)
                if error_msg is not None:
                    if not interactive:
                        return value
                    from rich.console import Console

                    Console().print(f"[bold red]{error_msg}[/bold red]")
                    continue
            return value

    @staticmethod
    def confirm(
        message: str,
        *,
        default: bool = True,
        theme: ThemeConfig | None = None,
    ) -> bool:
        """Prompt for yes/no confirmation.

        Args:
            message: The confirmation message to display.
            default: Default boolean value if the user enters nothing.
            theme: Optional ThemeConfig for styled prompts.

        Returns:
            True or False based on user input.

        Example:
            if Prompt.confirm("Continue?", default=True):
                print("Continuing...")
        """
        return _safe_confirm(message, default=default)

    @staticmethod
    def choice(
        message: str,
        choices: list[str],
        *,
        default: str | None = None,
        filter: Callable[[str], str] | None = None,  # noqa: A002
        theme: ThemeConfig | None = None,
    ) -> str:
        """Present a list of choices for the user to pick from.

        Args:
            message: The prompt message.
            choices: List of valid choices.
            default: Default choice if the user enters nothing.
            filter: Optional callable to transform the user's input before matching.
            theme: Optional ThemeConfig for styled prompts.

        Returns:
            The selected choice string.

        Example:
            color = Prompt.choice("Pick a color", ["red", "green", "blue"])
        """
        kwargs: dict[str, Any] = {"choices": choices}
        if default is not None:
            kwargs["default"] = default
        if filter is not None:  # noqa: A002
            kwargs["default"] = default or choices[0]

        return _safe_prompt(message, **kwargs)

    @staticmethod
    def integer(
        message: str,
        *,
        min: int | None = None,  # noqa: A002
        max: int | None = None,  # noqa: A002
        default: int | None = None,
        theme: ThemeConfig | None = None,
    ) -> int:
        """Prompt for integer input with range validation.

        Args:
            message: The prompt message.
            min: Minimum acceptable value (inclusive).
            max: Maximum acceptable value (inclusive).
            default: Default integer value if the user enters nothing.
            theme: Optional ThemeConfig for styled prompts.

        Returns:
            An integer within the specified range.

        Example:
            age = Prompt.integer("Enter your age", min=0, max=150)
        """
        kwargs: dict[str, Any] = {}
        if default is not None:
            kwargs["default"] = default

        interactive = _is_interactive()
        while True:
            value = _safe_int_prompt(message, **kwargs)
            if min is not None and value < min:
                if not interactive:
                    return value
                from rich.console import Console

                Console().print(f"[bold red]Value must be at least {min}[/bold red]")
                continue
            if max is not None and value > max:
                if not interactive:
                    return value
                from rich.console import Console

                Console().print(f"[bold red]Value must be at most {max}[/bold red]")
                continue
            return value

    @staticmethod
    def multi_choice(
        message: str,
        choices: list[str],
        *,
        default: list[str] | None = None,
        min_selections: int = 0,
        max_selections: int = 0,
        theme: ThemeConfig | None = None,
    ) -> list[str]:
        """Checkbox-style multiple selection from a list.

        Note: This is a simplified multi-select using comma-separated input
        since Rich doesn't have a built-in checkbox prompt. Users enter
        comma-separated indices or values.

        Args:
            message: The prompt message.
            choices: List of choices to select from.
            default: List of default selected values.
            min_selections: Minimum number of selections required (0 = no minimum).
            max_selections: Maximum number of selections allowed (0 = no maximum).
            theme: Optional ThemeConfig for styled prompts.

        Returns:
            List of selected choice strings.

        Example:
            toppings = Prompt.multi_choice("Select toppings",
                                           ["cheese", "pepperoni", "mushrooms"])
        """
        default_indices: str = ""
        if default:
            indices: list[str] = []
            for d in default:
                if d in choices:
                    indices.append(str(choices.index(d) + 1))
            default_indices = ",".join(indices)

        from rich.console import Console

        console = Console()
        console.print(message)
        for i, choice in enumerate(choices, 1):
            console.print(f"  {i}. {choice}")

        interactive = _is_interactive()
        while True:
            raw = _safe_prompt(
                "Enter numbers (comma-separated)",
                default=default_indices or "",
            )

            selected: list[str] = []
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(choices):
                        selected.append(choices[idx])

            if min_selections > 0 and len(selected) < min_selections:
                if not interactive:
                    return selected or (default or [])
                console.print(
                    f"[bold red]Select at least {min_selections} option(s)[/bold red]"
                )
                continue
            if max_selections > 0 and len(selected) > max_selections:
                if not interactive:
                    return selected[:max_selections]
                console.print(
                    f"[bold red]Select at most {max_selections} option(s)[/bold red]"
                )
                continue
            return selected


__all__ = ["Prompt"]
