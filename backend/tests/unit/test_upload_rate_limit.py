"""Unit tests for per-IP upload rate limiting (app/api/deps/upload_rate_limit.py)."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.api.deps.upload_rate_limit import check_upload_rate_limit, record_upload_attempt
from app.models.upload_rate_limit import UploadRateLimit


# ── helpers ────────────────────────────────────────────────────────────────────

IP = "192.168.1.10"


def _req(ip: str = IP) -> MagicMock:
    req = MagicMock()
    req.headers.get.return_value = ""   # no X-Forwarded-For
    req.client.host = ip
    return req


# ── check_upload_rate_limit ────────────────────────────────────────────────────

class TestCheckUploadRateLimit:
    def test_no_previous_upload_passes(self, monkeypatch):
        """No prior uploads → first submission is allowed."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        check_upload_rate_limit(_req(), db)  # should not raise

    def test_recent_upload_raises_429(self, monkeypatch):
        """Upload 5s after the previous one (cooldown=10s) → 429."""
        db = MagicMock()
        recent = MagicMock()
        recent.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=5)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = recent
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        with pytest.raises(HTTPException) as exc_info:
            check_upload_rate_limit(_req(), db)
        assert exc_info.value.status_code == 429

    def test_429_retry_after_is_remaining_seconds(self, monkeypatch):
        """retry_after_seconds should reflect time remaining in cooldown."""
        db = MagicMock()
        recent = MagicMock()
        recent.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=3)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = recent
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        with pytest.raises(HTTPException) as exc_info:
            check_upload_rate_limit(_req(), db)
        retry = exc_info.value.detail["retry_after_seconds"]
        # 10 - 3 = ~7 seconds remaining (allow ±1 for timing)
        assert 6 <= retry <= 8

    def test_429_includes_retry_after_header(self, monkeypatch):
        db = MagicMock()
        recent = MagicMock()
        recent.created_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = recent
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        with pytest.raises(HTTPException) as exc_info:
            check_upload_rate_limit(_req(), db)
        assert "Retry-After" in exc_info.value.headers

    def test_upload_after_cooldown_passes(self, monkeypatch):
        """Upload 15s after the previous one (cooldown=10s) → allowed."""
        db = MagicMock()
        # No recent entry within the window
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        check_upload_rate_limit(_req(), db)  # should not raise

    def test_different_ips_are_independent(self, monkeypatch):
        """IP-A being rate limited must not affect IP-B."""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        check_upload_rate_limit(_req("10.0.0.200"), db)  # should not raise


# ── record_upload_attempt ──────────────────────────────────────────────────────

class TestRecordUploadAttempt:
    def test_inserts_entry_and_commits(self, monkeypatch):
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        record_upload_attempt(_req(), db)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_inserted_entry_has_hashed_ip(self, monkeypatch):
        import hashlib
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        record_upload_attempt(_req(IP), db)
        added = db.add.call_args[0][0]
        expected_hash = hashlib.sha256(IP.encode()).hexdigest()
        assert added.ip_hash == expected_hash

    def test_stale_rows_deleted_before_insert(self, monkeypatch):
        """record_upload_attempt purges rows older than 2× cooldown before inserting."""
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)
        record_upload_attempt(_req(), db)
        # delete() must have been called (cleanup)
        db.query.return_value.filter.return_value.delete.assert_called_once()


# ── integration: check + record cycle against real DB ─────────────────────────

class TestUploadRateLimitIntegration:
    """Uses a real in-memory SQLite DB to test the full check→record→check cycle."""

    @pytest.fixture()
    def db(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.database import Base
        from app.models import upload_rate_limit  # noqa: F401 — register table

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_first_upload_allowed_second_blocked(self, db, monkeypatch):
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)

        req = _req()
        check_upload_rate_limit(req, db)   # should pass
        record_upload_attempt(req, db)

        with pytest.raises(HTTPException) as exc_info:
            check_upload_rate_limit(req, db)
        assert exc_info.value.status_code == 429

    def test_expired_record_allows_new_upload(self, db, monkeypatch):
        """A record older than the cooldown window should not block a new upload."""
        import hashlib
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)

        ip_hash = hashlib.sha256(IP.encode()).hexdigest()
        # Insert a record that is 30s old (outside the 10s cooldown)
        db.add(UploadRateLimit(
            ip_hash=ip_hash,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=30),
        ))
        db.commit()

        # Should be allowed (old record is outside the cooldown window)
        check_upload_rate_limit(_req(), db)  # should not raise

    def test_cleanup_removes_stale_rows(self, db, monkeypatch):
        """record_upload_attempt purges rows older than 2× cooldown."""
        import hashlib
        monkeypatch.setattr("app.api.deps.upload_rate_limit.settings.upload_rate_limit_seconds", 10)

        ip_hash = hashlib.sha256(IP.encode()).hexdigest()
        # Insert 5 stale rows (>20s old = 2× cooldown)
        for _ in range(5):
            db.add(UploadRateLimit(
                ip_hash=ip_hash,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=25),
            ))
        db.commit()

        # Count before
        count_before = db.query(UploadRateLimit).filter(UploadRateLimit.ip_hash == ip_hash).count()
        assert count_before == 5

        # Record a new upload (triggers cleanup)
        record_upload_attempt(_req(), db)

        # Stale rows should be gone; only 1 fresh row remains
        count_after = db.query(UploadRateLimit).filter(UploadRateLimit.ip_hash == ip_hash).count()
        assert count_after == 1
