"""Backward-compatible import shim for the canonical CLI package.

New code should import :mod:`smartvintaawesomekit.cli` or
:mod:`smartvintaawesomekit.cli.core`.
"""
from smartvintaawesomekit.cli.core import ProjectPlan, app

__all__ = ["ProjectPlan", "app"]
