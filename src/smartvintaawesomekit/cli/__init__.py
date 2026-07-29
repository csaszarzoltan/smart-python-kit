"""CLI Enhancement package — Rich-powered interactive prompts,
progress bars, colored output, tables, and skeleton generator.
"""

from __future__ import annotations

from smartvintaawesomekit.cli.commands import app as app
from smartvintaawesomekit.cli.theme import (
    ColorMode,
    ThemeConfig,
    error,
    get_console,
    info,
    panel,
    print,  # noqa: A004
    rule,
    stylize,
    success,
    warning,
)

__all__ = [
    "ColorMode",
    "ThemeConfig",
    "app",
    "error",
    "get_console",
    "info",
    "panel",
    "print",
    "rule",
    "stylize",
    "success",
    "warning",
]
