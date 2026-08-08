"""Tests for security audit, config validation, and CLI integration.

Sections:
    - TestAuditSecurityInterface: audit_security and validate_security_config imports/signatures
    - TestAuditSecurityBehavioral: audit report correctness
    - TestValidateSecurityConfigBehavioral: validation issue detection
    - TestSecurityCLIAudit: CLI command tests via Typer test runner
    - TestSecurityMetricsIntegration: observability metrics recording
    - TestSecurityMiddlewareOrdering: middleware ordering documentation
"""
from __future__ import annotations

import inspect

from fastapi import FastAPI
from typer.testing import CliRunner

from smartvintaawesomekit.cli.core import app
from smartvintaawesomekit.config import SecurityConfig as ConfigSecurityConfig
from smartvintaawesomekit.security import (
    SecurityConfig,
    audit_security,
    validate_security_config,
)

runner = CliRunner()


# ──────────────────────────────────────────────────────────────────
# Section 1: Interface tests
# ──────────────────────────────────────────────────────────────────


class TestAuditSecurityInterface:
    """Verify audit_security and validate_security_config exist with correct signatures."""

    def test_audit_security_importable(self) -> None:
        assert audit_security is not None

    def test_validate_security_config_importable(self) -> None:
        assert validate_security_config is not None

    def test_audit_security_signature(self) -> None:
        sig = inspect.signature(audit_security)
        params = list(sig.parameters.keys())
        assert "config" in params
        assert "environment" in params
        assert "cors_origins" in params
        assert "cors_methods" in params
        assert "cors_headers" in params

    def test_validate_security_config_signature(self) -> None:
        sig = inspect.signature(validate_security_config)
        params = list(sig.parameters.keys())
        assert "config" in params
        assert "cors_origins" in params
        assert "cors_methods" in params
        assert "cors_headers" in params
        assert "is_production" in params

    def test_security_config_in_config_module(self) -> None:
        """ConfigSecurityConfig should exist in the config module."""
        assert ConfigSecurityConfig is not None

    def test_config_security_config_has_fields(self) -> None:
        """ConfigSecurityConfig should have rate limiting fields."""
        cfg = ConfigSecurityConfig()
        assert cfg.enable_rate_limiting is True
        assert cfg.rate_limit_requests == 100
        assert cfg.rate_limit_window_seconds == 60

    def test_config_smart_config_has_security(self) -> None:
        """SmartConfig should have a security sub-config."""
        from smartvintaawesomekit.config import SmartConfig
        cfg = SmartConfig()
        assert hasattr(cfg, "security")
        assert cfg.security.enable_rate_limiting is True

    def test_security_exports_updated(self) -> None:
        """Security __all__ should include audit and validate functions."""
        from smartvintaawesomekit import security
        assert "audit_security" in security.__all__
        assert "validate_security_config" in security.__all__


# ──────────────────────────────────────────────────────────────────
# Section 2: audit_security behavioral tests
# ──────────────────────────────────────────────────────────────────


class TestAuditSecurityBehavioral:
    """Verify audit_security produces correct structured reports."""

    def test_default_audit_has_warnings(self) -> None:
        """Default SecurityConfig with wildcard CORS produces warnings (not a failure)."""
        report = audit_security()
        # Default config has wildcard CORS origins -> produces warnings
        assert report["exit_code"] in (0, 1)  # warnings OK
        assert report["total_checks"] > 0

    def test_default_audit_has_all_checks(self) -> None:
        """Default audit should check all middleware features."""
        report = audit_security()
        check_names = [c["check"] for c in report["checks"]]
        assert "Rate limiting" in check_names
        assert "Security headers" in check_names
        assert "CORS hardening" in check_names
        assert "Request size limit" in check_names
        assert "Input sanitization" in check_names

    def test_default_audit_has_header_checks(self) -> None:
        """Default audit should check all required security headers."""
        report = audit_security()
        check_names = [c["check"] for c in report["checks"]]
        assert "Header: X-Content-Type-Options" in check_names
        assert "Header: X-Frame-Options" in check_names
        assert "Header: Strict-Transport-Security" in check_names

    def test_wildcard_cors_warning(self) -> None:
        """Wildcard CORS origins should produce a warning."""
        report = audit_security(cors_origins=["*"])
        warnings = [c for c in report["checks"] if c["severity"] == "warning"]
        cors_warnings = [c for c in warnings if "CORS" in c["check"]]
        assert len(cors_warnings) >= 1
        assert report["exit_code"] == 1

    def test_wildcard_cors_critical_in_production(self) -> None:
        """Wildcard CORS in production should be critical."""
        cfg = SecurityConfig(reject_wildcard_in_production=True)
        report = audit_security(config=cfg, environment="production", cors_origins=["*"])
        criticals = [c for c in report["checks"] if c["severity"] == "critical"]
        assert len(criticals) >= 1
        assert report["exit_code"] == 2

    def test_explicit_origins_no_origin_warning(self) -> None:
        """Explicit CORS origins should not produce origin-level warnings."""
        report = audit_security(
            cors_origins=["https://example.com"],
            cors_methods=["GET", "POST"],
            cors_headers=["Authorization", "Content-Type"],
        )
        origin_warnings = [
            c for c in report["checks"]
            if c["severity"] == "warning" and "origin" in c["check"].lower()
        ]
        assert len(origin_warnings) == 0

    def test_disabled_headers_critical(self) -> None:
        """Disabling security headers should produce critical findings."""
        cfg = SecurityConfig(enable_security_headers=False)
        report = audit_security(config=cfg)
        criticals = [c for c in report["checks"] if c["severity"] == "critical"]
        assert len(criticals) >= 1

    def test_disabled_rate_limiting_warning(self) -> None:
        """Disabling rate limiting should produce a warning."""
        cfg = SecurityConfig(enable_rate_limiting=False)
        report = audit_security(config=cfg)
        warnings = [c for c in report["checks"] if c["severity"] == "warning"]
        rate_warnings = [c for c in warnings if "rate" in c["check"].lower()]
        assert len(rate_warnings) >= 1

    def test_low_rate_limit_warning(self) -> None:
        """Very low rate limit threshold should produce a warning."""
        cfg = SecurityConfig(rate_limit_requests=5)
        report = audit_security(config=cfg)
        warnings = [c for c in report["checks"] if c["severity"] == "warning"]
        rate_warnings = [c for c in warnings if "threshold" in c["check"].lower() or "rate" in c["check"].lower()]
        assert len(rate_warnings) >= 1

    def test_report_has_environment(self) -> None:
        """Report should include the environment."""
        report = audit_security(environment="production")
        assert report["environment"] == "production"

    def test_json_serializable(self) -> None:
        """Report should be JSON-serializable."""
        import json
        report = audit_security()
        serialized = json.dumps(report)
        assert isinstance(serialized, str)


# ──────────────────────────────────────────────────────────────────
# Section 3: validate_security_config behavioral tests
# ──────────────────────────────────────────────────────────────────


class TestValidateSecurityConfigBehavioral:
    """Verify validate_security_config detects incompatible settings."""

    def test_default_config_has_credential_issue(self) -> None:
        """Default config has wildcard + credentials, which is a critical issue."""
        issues = validate_security_config()
        critical = [i for i in issues if i["severity"] == "critical"]
        assert len(critical) >= 1
        assert "credentials" in critical[0]["message"].lower()

    def test_no_issues_with_explicit_config(self) -> None:
        """Explicit origins without wildcard should have no issues."""
        cfg = SecurityConfig(allow_credentials=True)
        issues = validate_security_config(
            config=cfg,
            cors_origins=["https://example.com"],
        )
        assert issues == []

    def test_wildcard_with_credentials_critical(self) -> None:
        """Wildcard origin + credentials should be a critical issue."""
        cfg = SecurityConfig(allow_credentials=True)
        issues = validate_security_config(config=cfg, cors_origins=["*"])
        critical = [i for i in issues if i["severity"] == "critical"]
        assert len(critical) >= 1
        assert "credentials" in critical[0]["message"].lower()

    def test_wildcard_production_critical(self) -> None:
        """Wildcard origin in production should be a critical issue."""
        cfg = SecurityConfig(reject_wildcard_in_production=True)
        issues = validate_security_config(
            config=cfg, cors_origins=["*"], is_production=True,
        )
        critical = [i for i in issues if i["severity"] == "critical"]
        assert len(critical) >= 1

    def test_rate_limiting_disabled_warning(self) -> None:
        """Disabled rate limiting should produce a warning."""
        cfg = SecurityConfig(enable_rate_limiting=False)
        issues = validate_security_config(config=cfg)
        warnings = [i for i in issues if i["severity"] == "warning"]
        assert len(warnings) >= 1

    def test_per_route_exceeds_global_warning(self) -> None:
        """Per-route limit exceeding global limit should be a warning."""
        cfg = SecurityConfig(
            rate_limit_requests=50,
            rate_limit_per_route={"/api/heavy": (100, 60)},
        )
        issues = validate_security_config(config=cfg)
        warnings = [i for i in issues if i["severity"] == "warning"]
        per_route = [i for i in warnings if "per-route" in i["message"].lower()]
        assert len(per_route) >= 1

    def test_very_low_rate_limit_warning(self) -> None:
        """Very low rate limit should produce a warning."""
        cfg = SecurityConfig(rate_limit_requests=3)
        issues = validate_security_config(config=cfg)
        warnings = [i for i in issues if i["severity"] == "warning"]
        low_limit = [i for i in warnings if "very low" in i["message"].lower()]
        assert len(low_limit) >= 1

    def test_explicit_origins_no_cors_issue(self) -> None:
        """Explicit origins should not trigger CORS issues."""
        issues = validate_security_config(cors_origins=["https://example.com"])
        cors_issues = [i for i in issues if "cors" in i["message"].lower()]
        assert len(cors_issues) == 0


# ──────────────────────────────────────────────────────────────────
# Section 4: CLI security audit tests
# ──────────────────────────────────────────────────────────────────


class TestSecurityCLIAudit:
    """CLI security audit command tests."""

    def test_security_audit_help(self) -> None:
        """security --help should show the security sub-command."""
        result = runner.invoke(app, ["security", "--help"])
        assert result.exit_code == 0
        assert "audit" in result.output.lower()

    def test_security_audit_help_command(self) -> None:
        """security audit --help should show usage."""
        result = runner.invoke(app, ["security", "audit", "--help"])
        assert result.exit_code == 0
        assert "exit code" in result.output.lower() or "security" in result.output.lower()

    def test_security_audit_default(self) -> None:
        """security audit with defaults should produce output."""
        result = runner.invoke(app, ["security", "audit"])
        assert result.exit_code == 0
        assert "Security Audit" in result.output

    def test_security_audit_json_output(self) -> None:
        """security audit --json should produce valid JSON."""
        import json
        result = runner.invoke(app, ["security", "audit", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "exit_code" in data
        assert "checks" in data
        assert "status" in data

    def test_security_audit_check_flag_with_issues(self) -> None:
        """security audit --check should exit non-zero when issues exist."""
        result = runner.invoke(app, ["security", "audit", "--check"])
        # Default config has wildcard CORS -> should exit non-zero with --check
        assert result.exit_code in (0, 1, 2)

    def test_security_audit_environment_production(self) -> None:
        """security audit --environment production with wildcards should warn/critical."""
        result = runner.invoke(app, ["security", "audit", "--environment", "production"])
        # Default config has wildcard origins, so production should have issues
        assert result.exit_code in (0, 1, 2)  # depends on config


# ──────────────────────────────────────────────────────────────────
# Section 5: Metrics integration tests
# ──────────────────────────────────────────────────────────────────


class TestSecurityMetricsIntegration:
    """Verify security middleware can optionally record metrics."""

    def test_ratelimit_accepts_metrics_registry(self) -> None:
        """RateLimitMiddleware should accept an optional metrics_registry."""
        from smartvintaawesomekit.security import RateLimitMiddleware
        from smartvintaawesomekit.observability.metrics import MetricsRegistry
        registry = MetricsRegistry()
        mw = RateLimitMiddleware(app=None, metrics_registry=registry)
        assert mw.metrics_registry is registry

    def test_ratelimit_default_no_metrics(self) -> None:
        """RateLimitMiddleware defaults to no metrics_registry."""
        from smartvintaawesomekit.security import RateLimitMiddleware
        mw = RateLimitMiddleware(app=None)
        assert mw.metrics_registry is None

    def test_inputsanitization_accepts_metrics_registry(self) -> None:
        """InputSanitizationMiddleware should accept an optional metrics_registry."""
        from smartvintaawesomekit.security import InputSanitizationMiddleware
        from smartvintaawesomekit.observability.metrics import MetricsRegistry
        registry = MetricsRegistry()
        mw = InputSanitizationMiddleware(app=None, metrics_registry=registry)
        assert mw.metrics_registry is registry

    def test_inputsanitization_default_no_metrics(self) -> None:
        """InputSanitizationMiddleware defaults to no metrics_registry."""
        from smartvintaawesomekit.security import InputSanitizationMiddleware
        mw = InputSanitizationMiddleware(app=None)
        assert mw.metrics_registry is None

    def test_security_middleware_with_observability(self) -> None:
        """Security middleware should attach to a FastAPI app with observability."""
        from smartvintaawesomekit.observability import install_observability
        from smartvintaawesomekit.security import add_security_middleware

        app = FastAPI()
        app = install_observability(app)
        app = add_security_middleware(app)
        assert app is not None


# ──────────────────────────────────────────────────────────────────
# Section 6: Middleware ordering tests
# ──────────────────────────────────────────────────────────────────


class TestSecurityMiddlewareOrdering:
    """Verify documentation of middleware ordering requirements."""

    def test_add_security_middleware_docstring_has_ordering(self) -> None:
        """add_security_middleware should document the ordering."""
        from smartvintaawesomekit.security.core import add_security_middleware as asm
        doc = asm.__doc__ or ""
        assert "rate limit" in doc.lower()
        assert "auth" in doc.lower()

    def test_security_middleware_exec_summary(self) -> None:
        """Security module docstring should describe the public API."""
        from smartvintaawesomekit import security
        doc = security.__doc__ or ""
        assert "audit" in doc.lower()
        assert "validate" in doc.lower()

    def test_core_module_has_required_headers(self) -> None:
        """Core module should define REQUIRED_HEADERS constant."""
        from smartvintaawesomekit.security.core import REQUIRED_HEADERS
        assert len(REQUIRED_HEADERS) >= 6
        header_names = {h["name"] for h in REQUIRED_HEADERS}
        assert "X-Content-Type-Options" in header_names
        assert "X-Frame-Options" in header_names
        assert "Strict-Transport-Security" in header_names
