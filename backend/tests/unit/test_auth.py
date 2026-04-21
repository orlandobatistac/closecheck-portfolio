"""Unit tests for the API key authentication dependency (app/api/deps/auth.py)."""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.api.deps.auth import verify_api_key


# ── helpers ────────────────────────────────────────────────────────────────────

def _req(key: str = "") -> MagicMock:
    """Build a minimal mock Request with the given X-API-Key header value."""
    req = MagicMock()
    req.headers.get.return_value = key
    req.url.path = "/api/v1/validate"
    return req


# ── tests: api_key_required = False (dev default) ─────────────────────────────

class TestApiKeyRequiredFalse:
    def test_no_header_passes(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", False)
        result = verify_api_key(_req(""))
        assert result == ""

    def test_any_header_passes(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", False)
        result = verify_api_key(_req("whatever"))
        assert result == ""

    def test_correct_header_passes(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", False)
        monkeypatch.setattr(auth.settings, "api_key", "my-secret")
        result = verify_api_key(_req("my-secret"))
        assert result == ""


# ── tests: api_key_required = True (production) ───────────────────────────────

class TestApiKeyRequiredTrue:
    def test_missing_header_raises_401(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "secret")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(_req(""))
        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    def test_whitespace_only_header_raises_401(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "secret")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(_req("   "))
        assert exc_info.value.status_code == 401

    def test_wrong_key_raises_401(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "secret")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(_req("wrong-key"))
        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    def test_correct_key_returns_key(self, monkeypatch):
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "secret")
        result = verify_api_key(_req("secret"))
        assert result == "secret"

    def test_leading_trailing_whitespace_stripped(self, monkeypatch):
        """Client sending key with accidental whitespace should be accepted."""
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "secret")
        result = verify_api_key(_req("  secret  "))
        assert result == "secret"

    def test_dev_key_default_rejected_when_required(self, monkeypatch):
        """Default 'dev-key' must not pass when a different production key is set."""
        from app.api.deps import auth
        monkeypatch.setattr(auth.settings, "api_key_required", True)
        monkeypatch.setattr(auth.settings, "api_key", "prod-secret-xyz")
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(_req("dev-key"))
        assert exc_info.value.status_code == 401
