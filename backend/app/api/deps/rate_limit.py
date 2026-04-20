"""
Demo rate limiting dependency.

Enforces two independent limits per 24-hour window (configurable):
  1. Session limit  — only one successful upload session per fingerprint.
  2. File count limit — cumulative file uploads across sessions must not exceed
                        settings.rate_limit_max_files.

Fingerprint is the union of:
  - SHA-256 hash of the real client IP address
  - SHA-256 hash of the X-Device-Token header (if supplied by the browser)

Either hash matching an existing entry in the window is sufficient to block the
request, making the limit hard to bypass with a simple refresh or IP rotation alone.

Rate limiting is skipped entirely when settings.demo_mode is False.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.rate_limit import RateLimitEntry


def _hash(value: str) -> str:
    """Return a hex SHA-256 digest of *value*."""
    return hashlib.sha256(value.encode()).hexdigest()


def _real_ip(request: Request) -> str:
    """Extract the real client IP, honouring X-Forwarded-For when present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the leftmost (originating) address only
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_demo_rate_limit(
    request: Request,
    file_count: int = 0,
    db: Session = Depends(get_db),
) -> None:
    """
    FastAPI dependency — raises HTTP 429 when a demo rate limit is exceeded.

    Parameters
    ----------
    file_count:
        Number of files in the current request.  Callers must supply this so
        the cumulative-file check can account for the *incoming* files before
        they are stored.  Defaults to 0 (safe for non-file endpoints).
    """
    if not settings.demo_mode:
        return

    window_start = datetime.now(timezone.utc) - timedelta(hours=settings.rate_limit_window_hours)
    # SQLite stores naive datetimes; strip tzinfo for the query
    window_start_naive = window_start.replace(tzinfo=None)

    ip_hash = _hash(_real_ip(request))
    raw_token = request.headers.get("X-Device-Token", "").strip()
    token_hash: str | None = _hash(raw_token) if raw_token else None

    # Build match condition: ip_hash match OR (token present AND token match)
    conditions = [RateLimitEntry.ip_hash == ip_hash]
    if token_hash:
        conditions.append(
            (RateLimitEntry.device_token_hash == token_hash)
        )

    recent_entries = (
        db.query(RateLimitEntry)
        .filter(
            RateLimitEntry.created_at >= window_start_naive,
            or_(*conditions),
        )
        .all()
    )

    retry_after_seconds = int(timedelta(hours=settings.rate_limit_window_hours).total_seconds())
    retry_after_iso = (
        datetime.now(timezone.utc) + timedelta(hours=settings.rate_limit_window_hours)
    ).isoformat()

    # ── Check 1: session limit ────────────────────────────────────────────────
    if recent_entries:
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(retry_after_seconds)},
            detail={
                "message": (
                    "You've already run a free analysis in the last "
                    f"{settings.rate_limit_window_hours} hours. "
                    "Come back tomorrow to run another check."
                ),
                "retry_after_seconds": retry_after_seconds,
                "retry_after_iso": retry_after_iso,
            },
        )

    # ── Check 2: cumulative file count limit ──────────────────────────────────
    used_files = sum(e.file_count for e in recent_entries)
    if used_files + file_count > settings.rate_limit_max_files:
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(retry_after_seconds)},
            detail={
                "message": (
                    f"You've reached the maximum of {settings.rate_limit_max_files} files "
                    f"allowed in a {settings.rate_limit_window_hours}-hour period. "
                    "Come back tomorrow to run another check."
                ),
                "retry_after_seconds": retry_after_seconds,
                "retry_after_iso": retry_after_iso,
            },
        )


def record_rate_limit_entry(
    request: Request,
    file_count: int,
    db: Session,
) -> None:
    """
    Insert a RateLimitEntry after a job has been successfully queued.
    Must be called *after* the job db.commit() so that only real queued jobs
    consume quota (not requests rejected for bad file types, etc.).
    """
    if not settings.demo_mode:
        return

    ip_hash = _hash(_real_ip(request))
    raw_token = request.headers.get("X-Device-Token", "").strip()
    token_hash: str | None = _hash(raw_token) if raw_token else None

    entry = RateLimitEntry(
        ip_hash=ip_hash,
        device_token_hash=token_hash,
        file_count=file_count,
    )
    db.add(entry)
    db.commit()
