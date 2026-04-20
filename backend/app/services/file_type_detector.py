"""
File type detection by magic bytes with extension fallback.

Normalizes any detected type to one of:
    "pdf" | "docx" | "image" | "html" | "xlsx" | "csv" | "txt" | "json" | "zip" | "unknown"
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Extension fallback map ────────────────────────────────────────────────────
_EXT_MAP: dict[str, str] = {
    ".pdf":   "pdf",
    ".docx":  "docx",
    ".doc":   "docx",   # handled best-effort by python-docx
    ".jpg":   "image",
    ".jpeg":  "image",
    ".png":   "image",
    ".gif":   "image",
    ".tiff":  "image",
    ".tif":   "image",
    ".bmp":   "image",
    ".webp":  "image",
    ".html":  "html",
    ".htm":   "html",
    ".xhtml": "html",
    ".xlsx":  "xlsx",
    ".xls":   "xlsx",   # converted via openpyxl best-effort
    ".csv":   "csv",
    ".tsv":   "csv",
    ".txt":   "txt",
    ".text":  "txt",
    ".md":    "txt",
    ".json":  "json",
    ".zip":   "zip",
}

# ── MIME → normalized type ────────────────────────────────────────────────────
_MIME_MAP: dict[str, str] = {
    "application/pdf":      "pdf",
    "application/zip":      "zip",
    "application/x-zip":    "zip",
    "application/x-zip-compressed": "zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/msword":   "docx",
    "application/vnd.ms-excel": "xlsx",
    "text/html":             "html",
    "application/xhtml+xml": "html",
    "text/csv":              "csv",
    "text/plain":            "txt",
    "application/json":      "json",
    "text/json":             "json",
    "image/jpeg":            "image",
    "image/png":             "image",
    "image/gif":             "image",
    "image/tiff":            "image",
    "image/bmp":             "image",
    "image/webp":            "image",
    "image/x-bmp":           "image",
}


def detect_file_type(path: Path) -> str:
    """
    Detect the normalized file type for *path*.

    Strategy:
    1. Try magic-byte detection via the `filetype` library.
    2. Fall back to file extension mapping.
    3. Return "unknown" if neither yields a known type.
    """
    # 1. Magic bytes
    try:
        import filetype as ft
        kind = ft.guess(str(path))
        if kind is not None:
            normalized = _MIME_MAP.get(kind.mime)
            if normalized:
                return normalized
    except Exception as exc:  # noqa: BLE001
        logger.debug("filetype magic detection failed for '%s': %s", path.name, exc)

    # 2. Extension fallback
    ext = path.suffix.lower()
    if ext in _EXT_MAP:
        return _EXT_MAP[ext]

    # 3. Peek at first bytes for ZIP/PDF signatures as last resort
    try:
        header = path.read_bytes()[:8]
        if header[:4] == b"PK\x03\x04":
            return "zip"
        if header[:4] == b"%PDF":
            return "pdf"
        # HTML heuristic
        if header.lstrip()[:1] in (b"<",):
            return "html"
    except OSError:
        pass

    logger.warning("Could not determine file type for '%s'", path.name)
    return "unknown"
