"""
AgentOps — Unit Tests for Authentication Logic
================================================
Tests password hashing, JWT token creation/decoding.
No network or database calls required.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

import pytest


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_is_not_plaintext(self):
        from app.core.security import hash_password
        hashed = hash_password("my_secret_password")
        assert hashed != "my_secret_password"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        from app.core.security import hash_password, verify_password
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        from app.core.security import hash_password, verify_password
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses a salt — same password should produce different hashes."""
        from app.core.security import hash_password
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_token_returns_string(self):
        from app.core.security import create_access_token
        token = create_access_token("user-id-123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_valid_token(self):
        from app.core.security import create_access_token, decode_access_token
        token = create_access_token("user-id-123", "test@example.com")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload.get("sub") == "user-id-123"

    def test_decode_invalid_token_returns_none(self):
        from app.core.security import decode_access_token
        result = decode_access_token("this.is.not.a.valid.token")
        assert result is None

    def test_decode_empty_string_returns_none(self):
        from app.core.security import decode_access_token
        result = decode_access_token("")
        assert result is None
