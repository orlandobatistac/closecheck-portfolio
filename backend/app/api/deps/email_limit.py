"""
Per-job email-draft rate limiting dependency.

Limits email drafts to settings.email_draft_limit_per_job per job per
IP fingerprint within a rolling settings.email_draft_window_hours window.
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps.rate_limit import _hash, _real_ip
from app.config import settings
from app.models.email_draft_limit import EmailDraftLimit

logger = logging.getLogger(__name__)


def check_email_draft_limit(job_id: str, request: Request, db: Session) -> None:
    """
    Raise HTTP 429 when this IP has reached the email draft quota for *job_id*.

    Must be called before the Claude API call so no tokens are spent on a
    request that will ultimately be rejected.
    """
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        hours=settings.email_draft_window_hours
    )
    ip_hash = _hash(_real_ip(request))

    recent_count = (
        db.query(EmailDraftLimit)
        .filter(
            EmailDraftLimit.job_id == job_id,
            EmailDraftLimit.ip_hash == ip_hash,
            EmailDraftLimit.created_at >= window_start,
        )
        .count()
    )

    if recent_count >= settings.email_draft_limit_per_job:
        retry_after = int(
            timedelta(hours=settings.email_draft_window_hours).total_seconds()
        )
        logger.warning(
            "Email draft limit reached for job %s (IP hash …%s): %d drafts in window",
            job_id,
            ip_hash[-8:],
            recent_count,
        )
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            detail={
                "message": (
                    f"You've reached the limit of {settings.email_draft_limit_per_job} "
                    f"email drafts for this job in a "
                    f"{settings.email_draft_window_hours}-hour period."
                ),
                "retry_after_seconds": retry_after,
            },
        )


def record_email_draft(job_id: str, request: Request, db: Session) -> None:
    """
    Persist a successful email draft record.

    Must be called *after* Claude returns successfully so that failed
    or rejected requests do not consume quota.
    """
    ip_hash = _hash(_real_ip(request))
    entry = EmailDraftLimit(job_id=job_id, ip_hash=ip_hash)
    db.add(entry)
    db.commit()
