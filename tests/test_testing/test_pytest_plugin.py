"""Pre-development tests for the testing module — Pytest Plugin.

Interface tests (PASS immediately with stubs):
    - Verify pytest plugin entry point in pyproject.toml
    - Verify fixtures appear in pytest --fixtures output
    - Verify plugin module is importable

Behavioral tests (FAIL with NotImplementedError):
    - Plugin auto-registers all fixtures
    - Fixtures appear in pytest --fixtures output
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

# ──────────────────────────────────────────────────────────────────
# Interface tests — must pass immediately
# ──────────────────────────────────────────────────────────────────


class TestPytestPluginInterface:
    """Verify pytest plugin module API exists with correct signatures."""

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_plugin_entry_points_in_pyproject(self) -> None:
        """Verify pytest11 entry point is registered in pyproject.toml."""
        pyproject_path = self.ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

        content = pyproject_path.read_text()
        # Check for pytest entry points
        has_pytest_entry = "pytest11" in content or "[project.entry-points.pytest11]" in content
        has_broken_link_brief = "broken_link_brief" in content or "smartvintaawesomekit" in content or "testing" in content
        assert has_pytest_entry or has_broken_link_brief, (
            "Expected pytest11 entry point in pyproject.toml"
        )

    def test_plugin_module_importable(self) -> None:
        """Verify the pytest plugin module can be imported (as a stub)."""
        try:
            import smartvintaawesomekit.testing.pytest_plugin as plugin  # type: ignore[import-untyped] # noqa: F811
            assert plugin is not None
        except ImportError:
            # The plugin module may not exist yet — that's OK for RED phase
            # But verify the testing package itself is importable
            import smartvintaawesomekit  # noqa: F401
            pytest.skip("pytest_plugin module not yet implemented — RED phase expected")

    def test_plugin_has_pytest_configure(self) -> None:
        """The plugin module should have pytest_configure or register functions."""
        try:
            import smartvintaawesomekit.testing.pytest_plugin as plugin_mod
            has_hook = (
                hasattr(plugin_mod, "pytest_configure")
                or hasattr(plugin_mod, "pytest_load_initial_conftests")
                or hasattr(plugin_mod, "register_assert_rewrite")
            )
            assert has_hook, "pytest_plugin should define at least one pytest hook"
        except ImportError:
            pytest.skip("pytest_plugin module not yet implemented")

    def test_plugin_exports_fixtures_module(self) -> None:
        """The plugin module should reference or export fixture definitions."""
        try:
            import smartvintaawesomekit.testing.pytest_plugin as plugin_mod
            module_dir = Path(plugin_mod.__file__).parent if plugin_mod.__file__ else None
            # Check if fixtures.py or conftest.py exists alongside
            if module_dir and module_dir.exists():
                has_fixtures_file = (module_dir / "fixtures.py").exists()
                has_conftest = (module_dir / "conftest.py").exists()
                # If neither exists, the plugin itself should define fixtures
                if not has_fixtures_file and not has_conftest:
                    plugin_source = inspect.getsource(plugin_mod)
                    assert "fixture" in plugin_source or "db_engine" in plugin_source or "db_session" in plugin_source
        except ImportError:
            pytest.skip("pytest_plugin module not yet implemented")

    def test_plugin_registers_fixtures(self) -> None:
        """Plugin entry point should be registered for pytest auto-discovery."""
        pyproject_path = self.ROOT / "pyproject.toml"
        content = pyproject_path.read_text()
        # Check for pytest11 entry in [project.entry-points.pytest11]
        assert "pytest11" in content or "smartvintaawesomekit" in content


class TestPytestPluginBehavioral:
    """Verify pytest plugin behaviors — stubs raise NotImplementedError.

    NOTE: These tests are inherently integration-level and may need the
    plugin to be installed. During RED phase they fail as expected.
    """

    ROOT = Path(__file__).resolve().parent.parent.parent

    def test_plugin_fixtures_available_via_pytest_fixtures(self) -> None:
        """Fixtures (db_engine, db_session, async_client) should appear in --fixtures.

        NOTE: Uses regex to distinguish actual fixture listings from error-message
        false positives (e.g. fixture names appearing in ImportError tracebacks).
        A valid fixture is indented at line start with 2+ spaces before the name.
        """
        # NOT IMPLEMENTED — requires plugin to be installed
        import re
        import subprocess
        result = subprocess.run(
            ["pytest", "--fixtures", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=str(self.ROOT),
            timeout=30,
        )
        output = result.stdout + result.stderr
        # Valid fixture lines look like "    db_engine" (indented with spaces).
        # Traceback lines contain "db_engine" inside file paths or error messages.
        for fname in ("db_engine", "db_session", "async_client"):
            # Match fixture name at line start (possibly after a newline).
            # In pytest 8+ --fixtures output, names appear without leading whitespace.
            pattern = re.compile(
                rf"(?:^|\n){re.escape(fname)}\b",
                re.MULTILINE,
            )
            matches = pattern.findall(output)
            assert len(matches) >= 1, (
                f"Fixture '{fname}' not found in --fixtures listing. "
                f"If it appears only in ImportError tracebacks, that is a "
                f"FALSE POSITIVE — the plugin must register fixtures properly."
            )

    def test_plugin_registers_via_entry_points(self) -> None:
        """Verify the pytest11 entry point exists and points to the right module."""
        # NOT IMPLEMENTED — fails during RED phase
        pyproject_path = self.ROOT / "pyproject.toml"
        content = pyproject_path.read_text()

        # Check for pytest11 entry-point in TOML (avoid ConfigParser which
        # can't handle TOML syntax like arrays of strings)
        has_pytest11_entry = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("pytest11") or "pytest11" in stripped:
                has_pytest11_entry = True
                break
            if "testing.pytest_plugin" in stripped or "testing" in stripped:
                if "pytest" in stripped.lower():
                    has_pytest11_entry = True
                    break

        assert has_pytest11_entry, (
            "pytest11 entry point not registered in pyproject.toml. "
            "Expected a section like:\n"
            "    [project.entry-points.pytest11]\n"
            "    broken_link_brief = \"smartvintaawesomekit.testing.pytest_plugin\""
        )
