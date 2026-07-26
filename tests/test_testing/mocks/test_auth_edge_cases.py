"""Edge-case and behavioral tests for Mock Auth classes.

Extends the pre-existing tests with coverage for:
- MockJWTManager: token format, decode round-trip, deterministic output
- MockPasswordHasher: verify same input → same hash, verify_password logic
- MockRBACManager: permission checks, role registration
- All mocks respond without side effects (no network, no DB)
"""

from __future__ import annotations

from smartvintaawesomekit.testing.mocks import (
    MockAuthConfig,
    MockJWTManager,
    MockPasswordHasher,
    MockRBACManager,
)

# ──────────────────────────────────────────────────────────────────
# MockJWTManager Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockJWTManagerEdgeCases:
    """Verify MockJWTManager edge cases."""

    def test_create_token_pair_deterministic(self) -> None:
        """create_token_pair() should return the same values each call."""
        from smartvintaawesomekit.auth.jwt import TokenPair

        mgr = MockJWTManager()
        pair1 = mgr.create_token_pair(subject="user1")
        pair2 = mgr.create_token_pair(subject="user2")  # subject ignored in mock
        assert isinstance(pair1, TokenPair)
        assert pair1.access_token == pair2.access_token  # both same (deterministic)
        assert pair1.refresh_token == pair2.refresh_token
        assert pair1.token_type == "bearer"
        assert pair1.expires_in == 1800

    def test_decode_token_returns_known_payload_structure(self) -> None:
        """decode_token() should return a payload dict with expected keys."""
        mgr = MockJWTManager()
        payload = mgr.decode_token(token="anything")
        assert "sub" in payload
        assert "type" in payload
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload
        assert payload["sub"] == "test-user-id"
        assert payload["type"] == "access"

    def test_decode_token_ignores_input(self) -> None:
        """decode_token() should return the same payload regardless of token value."""
        mgr = MockJWTManager()
        p1 = mgr.decode_token(token="token-a")
        p2 = mgr.decode_token(token="token-b")
        assert p1 == p2  # deterministic — ignores input

    def test_no_side_effects_between_calls(self) -> None:
        """Multiple operations on MockJWTManager should not change internal state."""
        mgr = MockJWTManager()
        pair = mgr.create_token_pair(subject="u1")
        payload = mgr.decode_token(token=pair.access_token)
        assert payload["sub"] == "test-user-id"  # fixed mock value

        # Second round
        pair2 = mgr.create_token_pair(subject="u2")
        assert pair2.access_token is not None


# ──────────────────────────────────────────────────────────────────
# MockPasswordHasher Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockPasswordHasherEdgeCases:
    """Verify MockPasswordHasher edge cases."""

    def test_hash_password_deterministic(self) -> None:
        """hash_password() should return the same hash for same input."""
        hasher = MockPasswordHasher()
        h1 = hasher.hash_password(password="hello")
        h2 = hasher.hash_password(password="hello")
        assert h1 == h2
        assert isinstance(h1, str)

    def test_hash_password_different_input_same_output(self) -> None:
        """hash_password() returns fixed hash regardless of input (mock behavior)."""
        hasher = MockPasswordHasher()
        h1 = hasher.hash_password(password="abc")
        h2 = hasher.hash_password(password="xyz")
        # Mock returns deterministic fixed string
        assert h1 == h2

    def test_verify_password_true_for_secret123(self) -> None:
        """verify_password() returns True only for 'secret123'."""
        hasher = MockPasswordHasher()
        hashed = hasher.hash_password(password="secret123")

        # The mock returns True only for password == "secret123"
        # Verify that specific behaviour
        assert hasher.verify_password(password="secret123", hashed=hashed) is True

    def test_verify_password_false_for_other(self) -> None:
        """verify_password() returns False for non-'secret123' passwords."""
        hasher = MockPasswordHasher()
        hashed = hasher.hash_password(password="secret123")
        assert hasher.verify_password(password="wrong", hashed=hashed) is False
        assert hasher.verify_password(password="", hashed=hashed) is False

    def test_verify_password_empty_string(self) -> None:
        """verify_password() should handle empty password."""
        hasher = MockPasswordHasher()
        hashed = hasher.hash_password(password="secret123")
        assert hasher.verify_password(password="", hashed=hashed) is False

    def test_verify_password_with_any_hash(self) -> None:
        """verify_password() ignores the hashed parameter (mock behaviour)."""
        hasher = MockPasswordHasher()
        assert hasher.verify_password(password="secret123", hashed="any_hash") is True
        assert hasher.verify_password(password="secret123", hashed="") is True

    def test_hash_password_returns_string(self) -> None:
        """hash_password() should always return a string."""
        hasher = MockPasswordHasher()
        assert isinstance(hasher.hash_password(password="test"), str)
        assert isinstance(hasher.hash_password(password=""), str)
        assert len(hasher.hash_password(password="test")) > 0


# ──────────────────────────────────────────────────────────────────
# MockRBACManager Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockRBACManagerEdgeCases:
    """Verify MockRBACManager edge cases."""

    def test_check_permission_always_true(self) -> None:
        """check_permission() should return True regardless of inputs."""
        mgr = MockRBACManager()
        assert mgr.check_permission(user_id=1, permission="read") is True
        assert mgr.check_permission(user_id=None, permission=None) is True
        assert mgr.check_permission(user_id="any", permission="anything") is True
        assert mgr.check_permission() is True  # no args

    def test_get_user_roles_returns_list_of_strings(self) -> None:
        """get_user_roles() should return a list of strings."""
        mgr = MockRBACManager()
        roles = mgr.get_user_roles(user_id=1)
        assert isinstance(roles, list)
        assert all(isinstance(r, str) for r in roles)

    def test_get_user_roles_deterministic(self) -> None:
        """get_user_roles() should return the same list regardless of user_id."""
        mgr = MockRBACManager()
        r1 = mgr.get_user_roles(user_id=1)
        r2 = mgr.get_user_roles(user_id=999)
        assert r1 == r2

    def test_no_side_effects(self) -> None:
        """MockRBACManager should not accumulate state across calls."""
        mgr = MockRBACManager()
        mgr.check_permission(user_id=1, permission="admin")
        mgr.get_user_roles(user_id=1)
        # After any number of calls, behaviour should be the same
        assert mgr.check_permission() is True
        assert mgr.get_user_roles(user_id=1) == ["user"]


# ──────────────────────────────────────────────────────────────────
# MockAuthConfig Edge Cases
# ──────────────────────────────────────────────────────────────────


class TestMockAuthConfigEdgeCases:
    """Verify MockAuthConfig edge cases."""

    def test_default_values(self) -> None:
        """MockAuthConfig should have test-safe defaults."""
        config = MockAuthConfig()
        assert config.jwt_secret_key == "test-secret-key-not-for-production"
        assert config.jwt_algorithm == "HS256"

    def test_custom_secret_key(self) -> None:
        """MockAuthConfig should accept custom secret key."""
        config = MockAuthConfig(jwt_secret_key="custom")
        assert config.jwt_secret_key == "custom"
        assert config.jwt_algorithm == "HS256"  # unchanged

    def test_custom_algorithm(self) -> None:
        """MockAuthConfig should accept custom algorithm."""
        config = MockAuthConfig(jwt_algorithm="RS256")
        assert config.jwt_algorithm == "RS256"

    def test_is_authconfig_subclass(self) -> None:
        """MockAuthConfig should be a subclass of AuthConfig."""
        from smartvintaawesomekit.auth.config import AuthConfig
        assert issubclass(MockAuthConfig, AuthConfig)
