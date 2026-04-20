"""
SHA-256-based deduplication for ingested file lists.
"""
import logging
from pathlib import Path

from app.services.extractors import compute_sha256

logger = logging.getLogger(__name__)


def deduplicate(paths: list[Path]) -> tuple[list[Path], list[str]]:
    """
    Remove duplicate files (by SHA-256) from *paths*.

    Returns:
        unique_paths: Deduplicated list preserving original order.
        warnings:     Human-readable messages for each skipped duplicate.
    """
    seen: dict[str, Path] = {}
    unique: list[Path] = []
    warnings: list[str] = []

    for path in paths:
        try:
            digest = compute_sha256(path)
        except OSError as exc:
            warnings.append(f"Could not hash '{path.name}' for dedup check: {exc}")
            unique.append(path)
            continue

        if digest in seen:
            original = seen[digest]
            msg = (
                f"Duplicate file skipped: '{path.name}' is identical to "
                f"'{original.name}' (sha256={digest[:12]}…)"
            )
            logger.info(msg)
            warnings.append(msg)
        else:
            seen[digest] = path
            unique.append(path)

    return unique, warnings
