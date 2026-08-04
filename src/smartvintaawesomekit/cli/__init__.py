"""Canonical SmartVintaAwesomeKit command-line interface.

The package exports the lifecycle CLI from :mod:`smartvintaawesomekit.cli.core`.
Visual helper modules remain importable for backward compatibility.
"""
from smartvintaawesomekit.cli.core import ProjectPlan, app

__all__ = ["ProjectPlan", "app"]
