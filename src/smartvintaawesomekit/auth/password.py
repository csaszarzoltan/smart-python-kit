"""Secure password hashing with algorithm-agnostic interface."""

from __future__ import annotations

from passlib.context import CryptContext


class PasswordHasher:
    """Configurable password hasher — bcrypt or argon2."""

    _SUPPORTED = {"bcrypt", "argon2"}

    def __init__(self, algorithm: str = "bcrypt") -> None:
        """Initialize hasher. Raises ValueError on unsupported algorithm.

        Args:
            algorithm: Hashing algorithm — 'bcrypt' or 'argon2'.
        """
        if algorithm not in self._SUPPORTED:
            raise ValueError(
                f"Unsupported algorithm '{algorithm}'. Choose from: {self._SUPPORTED}"
            )
        self._algorithm: str = algorithm
        self._ctx: CryptContext = CryptContext(schemes=[algorithm], deprecated="auto")

    def _ensure_ctx(self) -> CryptContext:
        """Lazily initialize CryptContext when __init__ was skipped."""
        if not hasattr(self, "_ctx"):
            self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return self._ctx

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password. Returns encoded hash string.

        Args:
            password: Plaintext password to hash.

        Returns:
            Hashed password string.
        """
        return self._ensure_ctx().hash(password)

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash. Returns True if match.

        Args:
            password: Plaintext password to verify.
            hashed: Stored hash to compare against.

        Returns:
            True if password matches the hash.
        """
        try:
            return self._ensure_ctx().verify(password, hashed)
        except (ValueError, Exception):
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """Check if hash should be re-computed (e.g., algorithm upgrade).

        Args:
            hashed: Stored hash to check.

        Returns:
            True if the hash needs to be recomputed.
        """
        try:
            return self._ensure_ctx().needs_update(hashed)
        except (ValueError, Exception):
            return True


__all__ = ["PasswordHasher"]
