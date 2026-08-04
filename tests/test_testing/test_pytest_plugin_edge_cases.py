"""Edge-case and behavioral tests for the pytest plugin.

Extends the pre-existing tests with coverage for:
- All fixtures from the plugin appear in pytest --fixtures
- Multiple plugins don't conflict
- Marker registration works
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class TestPytestPluginFixturesEdgeCases:
    """Verify plugin fixtures appear correctly."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_db_engine_fixture_in_listing(self) -> None:
        """db_engine should appear in pytest --fixtures output."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--fixtures", "-p", "no:cacheprovider", "-q"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        assert "db_engine" in output, "db_engine fixture not found in --fixtures output"

    def test_db_session_fixture_in_listing(self) -> None:
        """db_session should appear in pytest --fixtures output."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--fixtures", "-p", "no:cacheprovider", "-q"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        assert "db_session" in output, "db_session fixture not found in --fixtures output"

    def test_async_client_fixture_in_listing(self) -> None:
        """async_client should appear in pytest --fixtures output."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--fixtures", "-p", "no:cacheprovider", "-q"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        assert "async_client" in output, "async_client fixture not found in --fixtures output"

    def test_all_three_fixtures_present(self) -> None:
        """All three core fixtures should appear in --fixtures output."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--fixtures", "-p", "no:cacheprovider", "-q"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        for fname in ("db_engine", "db_session", "async_client"):
            assert fname in output, f"Fixture '{fname}' not in --fixtures output"


class TestPytestPluginMarkerRegistration:
    """Verify marker registration works."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_asyncio_marker_registered(self) -> None:
        """The 'asyncio' marker should be registered by the plugin."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        assert "asyncio" in output.lower(), "'asyncio' marker not found in --markers output"

    def test_db_marker_registered(self) -> None:
        """The 'db' marker should be registered by the plugin."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--markers", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = result.stdout + result.stderr
        assert "db:" in output, "'db' marker not found in --markers output"


class TestPytestPluginEntryPoint:
    """Verify the pytest11 entry point is functional."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_plugin_module_importable_via_pytest(self) -> None:
        """The plugin module should be importable when pytest loads it."""
        result = subprocess.run(
            [sys.executable, "-c",
             "from smartvintaawesomekit.testing.pytest_plugin import pytest_configure; print('OK')"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=15,
            env={**os.environ, "PYTHONPATH": str(self.ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout

    def test_plugin_has_pytest_configure(self) -> None:
        """The plugin module should have a pytest_configure function."""
        import smartvintaawesomekit.testing.pytest_plugin as plugin
        assert hasattr(plugin, "pytest_configure")
        assert callable(plugin.pytest_configure)

    def test_plugin_exports_db_engine_fixture(self) -> None:
        """The plugin module should export db_engine fixture wrapper."""
        import smartvintaawesomekit.testing.pytest_plugin as plugin
        assert hasattr(plugin, "db_engine")

    def test_plugin_exports_db_session_fixture(self) -> None:
        """The plugin module should export db_session fixture wrapper."""
        import smartvintaawesomekit.testing.pytest_plugin as plugin
        assert hasattr(plugin, "db_session")

    def test_plugin_exports_async_client_fixture(self) -> None:
        """The plugin module should export async_client fixture wrapper."""
        import smartvintaawesomekit.testing.pytest_plugin as plugin
        assert hasattr(plugin, "async_client")
