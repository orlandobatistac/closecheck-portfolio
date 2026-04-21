"""
API key authentication dependency.

Validates the X-API-Key header against settings.api_key.

Enabled when settings.api_key_required is True.  When False (dev default)
the check is skipped entirely — safe for local development without any
token configured in .env.
"""
import logging

from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)


def verify_api_key(request: Request) -> str:
    """
    FastAPI dependency — validates the X-API-Key header.

    When settings.api_key_required is False the check is bypassed and an
    empty string is returned so callers don't need to change signature.

    Returns the validated key string on success.
    Raises HTTP 401 when the header is missing or does not match.
    """
    if not settings.api_key_required:
        return ""

    provided = request.headers.get("X-API-Key", "").strip()

    if not provided:
        logger.warning(
            "Request to %s rejected: missing X-API-Key header", request.url.path
        )
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include an 'X-API-Key' header in your request.",
        )

    if provided != settings.api_key:
        logger.warning(
            "Request to %s rejected: invalid X-API-Key supplied", request.url.path
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return provided
