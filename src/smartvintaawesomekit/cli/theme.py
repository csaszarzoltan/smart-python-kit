"""Colored output and theme system for CLI.

Provides ColorMode detection, ThemeConfig (pydantic-settings), and helper functions
for consistent colored output across all CLI modules.

Usage:
    from smartvintaawesomekit.cli.theme import info, success, error, print, stylize

    info("Processing complete")
    success("Deployment succeeded")
    error("Connection failed")
    stylize("Important", "bold yellow")
    print("Custom styled output", style="bold magenta")
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic_settings import BaseSettings
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

# Module-level cache for the shared console
_console: Console | None = None


class ColorMode(enum.Enum):
    """Color output mode based on terminal capabilities."""

    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"
    FORCE_COLOR = "force_color"
    NO_COLOR = "no_color"


class ThemeConfig(BaseSettings):
    """Theme configuration loaded from environment variables and user config.

    Prefix: CLI_THEME_

    Usage:
        config = ThemeConfig()
        console = config.to_console()
        console.print("Hello", style=config.primary)
    """

    mode: ColorMode = ColorMode.AUTO
    primary: str = "bold cyan"
    secondary: str = "dim white"
    success: str = "bold green"
    error: str = "bold red"
    warning: str = "bold yellow"
    info: str = "blue"
    muted: str = "grey50"
    prompt: str = "bold cyan"
    highlight: str = "yellow"
    progress_bar: str = "cyan"
    progress_percent: str = "green"
    table_header: str = "bold magenta"
    table_border: str = "dim"
    table_alt_rows: str = "dim on default"

    model_config = {"env_prefix": "CLI_THEME_"}

    def to_rich_theme(self) -> Theme:
        """Convert to a Rich Theme object for use with Console.

        Returns:
            A rich.theme.Theme instance mapping style names to style definitions.
        """
        style_map: dict[str, str] = {
            "primary": self.primary,
            "secondary": self.secondary,
            "success": self.success,
            "error": self.error,
            "warning": self.warning,
            "info": self.info,
            "muted": self.muted,
            "prompt": self.prompt,
            "highlight": self.highlight,
            "progress.bar": self.progress_bar,
            "progress.percent": self.progress_percent,
            "table.header": self.table_header,
            "table.border": self.table_border,
            "table.alt_rows": self.table_alt_rows,
        }
        return Theme(style_map)

    def to_console(self) -> Console:
        """Create a Rich Console configured with this theme and color mode.

        Returns:
            A rich.console.Console instance respecting the current theme and color mode.
        """
        force_terminal: bool | None = None
        no_color: bool | None = None

        if self.mode == ColorMode.FORCE_COLOR:
            force_terminal = True
            no_color = False
        elif self.mode == ColorMode.NO_COLOR:
            no_color = True
            force_terminal = None
        elif self.mode in (ColorMode.LIGHT, ColorMode.DARK):
            force_terminal = True

        return Console(
            theme=self.to_rich_theme(),
            force_terminal=force_terminal,
            no_color=no_color,
        )


def get_console(*, force_mode: ColorMode | None = None) -> Console:
    """Get a shared Rich Console instance respecting the global theme.

    Args:
        force_mode: Optional override for the color mode. When provided, creates
                    a new console with the forced mode on every call.

    Returns:
        A shared or freshly-created rich.console.Console instance.

    Example:
        console = get_console()
        console.print("Hello World", style="bold green")
    """
    global _console
    if force_mode is not None:
        config = ThemeConfig(mode=force_mode)
        return config.to_console()
    if _console is None:
        _console = ThemeConfig().to_console()
    return _console


def stylize(text: str, style: str) -> str:
    """Return a stylized string without printing.

    Args:
        text: The text to style.
        style: A Rich-style format string (e.g. "bold red", "blue on white").

    Returns:
        The text wrapped in Rich markup for the given style.

    Example:
        output = stylize("Important message", "bold red")
        print(output)
    """
    return str(Text(text, style=style))


def print(  # noqa: A001 — intentionally shadows built-in print
    *values: object,
    sep: str = " ",
    end: str = "\n",
    style: str | None = None,
    **console_kwargs: Any,  # noqa: ANN401 — forwarded to rich.console.Console.print()
) -> None:
    """Enhanced print using the themed Console.

    Args:
        *values: Values to print.
        sep: Separator between values (default: " ").
        end: String appended after the last value (default: "\\n").
        style: Optional Rich style string to apply to the entire output.
        **console_kwargs: Additional keyword arguments forwarded to rich.console.Console.print().

    Example:
        print("Hello", "World", style="bold cyan")
    """
    console = get_console()
    console.print(*values, sep=sep, end=end, style=style, **console_kwargs)


def success(message: str) -> None:
    """Print a success message with green checkmark.

    Args:
        message: The success message to display.

    Example:
        success("Deployment completed successfully")
    """
    console = get_console()
    console.print(f"✓ {message}", style="bold green")


def error(message: str) -> None:
    """Print an error message with red X.

    Args:
        message: The error message to display.

    Example:
        error("Failed to connect to database")
    """
    console = get_console()
    console.print(f"✗ {message}", style="bold red")


def warning(message: str) -> None:
    """Print a warning message with yellow triangle.

    Args:
        message: The warning message to display.

    Example:
        warning("Disk space is low")
    """
    console = get_console()
    console.print(f"⚠ {message}", style="bold yellow")


def info(message: str) -> None:
    """Print an info message with blue 'i'.

    Args:
        message: The info message to display.

    Example:
        info("Processing 42 records")
    """
    console = get_console()
    console.print(f"ℹ {message}", style="blue")


def panel(title: str, content: str, *, style: str | None = None) -> None:
    """Render content inside a Rich Panel with optional title.

    Args:
        title: The panel title text.
        content: The content to display inside the panel.
        style: Optional Rich style for the panel border.

    Example:
        panel("Summary", "All tasks completed successfully", style="bold green")
    """
    console = get_console()
    console.print(Panel(content, title=title, border_style=style or ""))


def rule(title: str = "", *, style: str | None = None) -> None:
    """Render a horizontal rule/separator with optional title text.

    Args:
        title: Optional title text displayed in the rule.
        style: Optional Rich style for the rule character.

    Example:
        rule("Section 1", style="dim")
    """
    console = get_console()
    console.print(Rule(title=title, style=style or ""))


__all__ = [
    "ColorMode",
    "ThemeConfig",
    "get_console",
    "stylize",
    "print",
    "success",
    "error",
    "warning",
    "info",
    "panel",
    "rule",
]
