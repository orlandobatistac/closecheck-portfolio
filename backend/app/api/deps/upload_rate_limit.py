"""
Per-IP upload-submission rate limiting dependency.

Enforces a minimum gap of settings.upload_rate_limit_seconds between
consecutive uploads from the same IP address.  Intended to prevent rapid
automated re-submission without affecting normal human usage.
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps.rate_limit import _hash, _real_ip
from app.config import settings
from app.models.upload_rate_limit import UploadRateLimit

logger = logging.getLogger(__name__)


def check_upload_rate_limit(request: Request, db: Session) -> None:
    """
    Raise HTTP 429 when this IP has uploaded within the cooldown window.

    Call at the very start of the upload handler, before any file processing,
    so storage and Claude tokens are never consumed for a blocked request.
    """
    cooldown = settings.upload_rate_limit_seconds
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=cooldown)
    ip_hash = _hash(_real_ip(request))

    recent = (
        db.query(UploadRateLimit)
        .filter(
            UploadRateLimit.ip_hash == ip_hash,
            UploadRateLimit.created_at >= window_start,
        )
        .order_by(UploadRateLimit.created_at.desc())
        .first()
    )

    if recent is not None:
        elapsed = (datetime.now(timezone.utc).replace(tzinfo=None) - recent.created_at).total_seconds()
        retry_after = max(1, int(cooldown - elapsed))
        logger.warning(
            "Upload rate limit hit for IP …%s — retry in %ds",
            ip_hash[-8:],
            retry_after,
        )
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            detail={
                "message": (
                    f"Please wait {retry_after} second(s) before submitting another job."
                ),
                "retry_after_seconds": retry_after,
            },
        )


def record_upload_attempt(request: Request, db: Session) -> None:
    """
    Persist a successful upload submission record.

    Must be called *after* the job has been queued so that requests rejected
    for bad content-type or file count do not consume a slot.

    Also purges stale rows for this IP (older than 2× the cooldown window)
    to keep the table from growing unboundedly.
    """
    ip_hash = _hash(_real_ip(request))
    cooldown = settings.upload_rate_limit_seconds

    # Cleanup stale rows for this IP only
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=cooldown * 2)
    db.query(UploadRateLimit).filter(
        UploadRateLimit.ip_hash == ip_hash,
        UploadRateLimit.created_at < cutoff,
    ).delete(synchronize_session=False)

    db.add(UploadRateLimit(ip_hash=ip_hash))
    db.commit()
