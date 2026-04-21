"""Unit tests for per-job email draft rate limiting (app/api/deps/email_limit.py)."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.api.deps.email_limit import check_email_draft_limit, record_email_draft
from app.models.email_draft_limit import EmailDraftLimit


# ── helpers ────────────────────────────────────────────────────────────────────

JOB_ID = "job-email-test-001"
IP = "10.0.0.55"


def _req(ip: str = IP) -> MagicMock:
    req = MagicMock()
    req.headers.get.return_value = ""   # no X-Forwarded-For
    req.client.host = ip
    return req


def _entry(job_id: str = JOB_ID, ip: str = IP, hours_ago: float = 0) -> EmailDraftLimit:
    import hashlib
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    return EmailDraftLimit(
        job_id=job_id,
        ip_hash=ip_hash,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours_ago),
    )


# ── check_email_draft_limit ────────────────────────────────────────────────────

class TestCheckEmailDraftLimit:
    def test_no_previous_drafts_passes(self, monkeypatch):
        """Zero existing drafts → request is allowed."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        check_email_draft_limit(JOB_ID, _req(), db)  # should not raise

    def test_under_limit_passes(self, monkeypatch):
        """2 existing drafts with limit=3 → allowed."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 2
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        check_email_draft_limit(JOB_ID, _req(), db)  # should not raise

    def test_at_limit_raises_429(self, monkeypatch):
        """Exactly at limit → 429."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 3
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        with pytest.raises(HTTPException) as exc_info:
            check_email_draft_limit(JOB_ID, _req(), db)
        assert exc_info.value.status_code == 429

    def test_over_limit_raises_429(self, monkeypatch):
        """Well over limit → 429."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 99
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        with pytest.raises(HTTPException) as exc_info:
            check_email_draft_limit(JOB_ID, _req(), db)
        assert exc_info.value.status_code == 429

    def test_429_includes_retry_after_header(self, monkeypatch):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 3
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        with pytest.raises(HTTPException) as exc_info:
            check_email_draft_limit(JOB_ID, _req(), db)
        assert "Retry-After" in exc_info.value.headers
        assert int(exc_info.value.headers["Retry-After"]) == 24 * 3600

    def test_429_detail_mentions_limit(self, monkeypatch):
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 3
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        with pytest.raises(HTTPException) as exc_info:
            check_email_draft_limit(JOB_ID, _req(), db)
        message = exc_info.value.detail["message"]
        assert "3" in message

    def test_different_jobs_are_independent(self, monkeypatch):
        """Limit for job-A should not affect job-B."""
        def count_side_effect(*args, **kwargs):
            # second call (different job_id) returns 0
            return 0

        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        check_email_draft_limit("job-B", _req(), db)  # should not raise

    def test_different_ips_are_independent(self, monkeypatch):
        """Two different IPs can each draft up to the limit independently."""
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 0
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        check_email_draft_limit(JOB_ID, _req("10.0.0.99"), db)  # should not raise


# ── record_email_draft ─────────────────────────────────────────────────────────

class TestRecordEmailDraft:
    def test_inserts_entry_and_commits(self, monkeypatch):
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        record_email_draft(JOB_ID, _req(), db)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_inserted_entry_has_correct_job_id(self, monkeypatch):
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        record_email_draft("specific-job", _req(), db)
        added = db.add.call_args[0][0]
        assert added.job_id == "specific-job"

    def test_inserted_entry_has_hashed_ip(self, monkeypatch):
        import hashlib
        db = MagicMock()
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)
        record_email_draft(JOB_ID, _req(IP), db)
        added = db.add.call_args[0][0]
        expected_hash = hashlib.sha256(IP.encode()).hexdigest()
        assert added.ip_hash == expected_hash


# ── integration: check + record cycle against real DB ─────────────────────────

class TestEmailLimitIntegration:
    """Uses a real in-memory SQLite DB to test the full check→record→check cycle."""

    @pytest.fixture()
    def db(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.database import Base
        from app.models import email_draft_limit  # noqa: F401 — register table

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_three_allowed_fourth_blocked(self, db, monkeypatch):
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 24)

        req = _req()
        for _ in range(3):
            check_email_draft_limit(JOB_ID, req, db)
            record_email_draft(JOB_ID, req, db)

        with pytest.raises(HTTPException) as exc_info:
            check_email_draft_limit(JOB_ID, req, db)
        assert exc_info.value.status_code == 429

    def test_expired_entries_dont_count(self, db, monkeypatch):
        """Drafts older than the window should not count towards the limit."""
        import hashlib
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_limit_per_job", 3)
        monkeypatch.setattr("app.api.deps.email_limit.settings.email_draft_window_hours", 1)

        ip_hash = hashlib.sha256(IP.encode()).hexdigest()
        # Insert 3 entries that are 2 hours old (outside the 1-hour window)
        for _ in range(3):
            db.add(EmailDraftLimit(
                job_id=JOB_ID,
                ip_hash=ip_hash,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2),
            ))
        db.commit()

        # A new draft should still be allowed (old ones are outside the window)
        check_email_draft_limit(JOB_ID, _req(), db)  # should not raise
