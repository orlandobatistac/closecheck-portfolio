"""
Extractors package — modular document parsing with a unified output schema.

Public API:
    ParsedDocument  — normalized output dataclass
    BaseExtractor   — abstract base for all format extractors
    extract_document(path, file_type) → ParsedDocument
    EXTRACTOR_REGISTRY — maps file_type string → extractor class
"""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Normalized output schema ───────────────────────────────────────────────────

@dataclass
class ParsedDocument:
    """
    Common schema produced by every extractor.

    Attributes:
        filename:           Original filename (not full path).
        file_type:          Detected type: "pdf", "docx", "image", "html",
                            "xlsx", "csv", "txt", "json", "zip".
        text:               Normalized plain text ready for LLM consumption.
        metadata:           Format-specific metadata (pages, sheets, …).
        extraction_method:  "native", "ocr-vision", or extractor-specific label.
        warnings:           Non-fatal issues encountered during extraction.
        sha256:             Hex digest of the file's raw bytes (for dedup).
        source_archive:     Name of the ZIP this was extracted from, if any.
    """
    filename: str
    file_type: str
    text: str
    metadata: dict = field(default_factory=dict)
    extraction_method: str = "native"
    warnings: list[str] = field(default_factory=list)
    sha256: str = ""
    source_archive: Optional[str] = None


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseExtractor(ABC):
    """All format extractors must inherit this class and implement `extract`."""

    @abstractmethod
    def extract(self, path: Path) -> ParsedDocument:
        """
        Parse *path* and return a fully populated ParsedDocument.

        Implementations must:
        - Never raise for corrupt/partial files; append to `warnings` instead.
        - Always populate `sha256` via `compute_sha256(path)`.
        - Set `extraction_method` to a descriptive string.
        """


# ── Extractor registry ────────────────────────────────────────────────────────

#: Maps normalized file_type string → extractor class.
#: Populated lazily on first call to avoid circular-import issues.
EXTRACTOR_REGISTRY: dict[str, type[BaseExtractor]] = {}


def _build_registry() -> None:
    from app.services.extractors.pdf_extractor import PDFExtractor
    from app.services.extractors.docx_extractor import DOCXExtractor
    from app.services.extractors.image_extractor import ImageExtractor
    from app.services.extractors.html_extractor import HTMLExtractor
    from app.services.extractors.xlsx_extractor import XLSXExtractor
    from app.services.extractors.csv_extractor import CSVExtractor
    from app.services.extractors.txt_extractor import TXTExtractor
    from app.services.extractors.json_extractor import JSONExtractor

    EXTRACTOR_REGISTRY.update({
        "pdf":   PDFExtractor,
        "docx":  DOCXExtractor,
        "image": ImageExtractor,
        "html":  HTMLExtractor,
        "xlsx":  XLSXExtractor,
        "csv":   CSVExtractor,
        "txt":   TXTExtractor,
        "json":  JSONExtractor,
    })


# ── Public helpers ────────────────────────────────────────────────────────────

def compute_sha256(path: Path) -> str:
    """Return hex SHA-256 digest of *path*'s raw bytes."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_document(
    path: Path,
    file_type: str,
    source_archive: Optional[str] = None,
) -> ParsedDocument:
    """
    Route *path* to the appropriate extractor and return a ParsedDocument.

    If the file_type has no registered extractor, falls back to TXTExtractor
    and records a warning.

    Args:
        path:           Absolute path to the file to parse.
        file_type:      Normalized type string (see EXTRACTOR_REGISTRY keys).
        source_archive: ZIP filename this file was extracted from, if any.
    """
    if not EXTRACTOR_REGISTRY:
        _build_registry()

    extractor_cls = EXTRACTOR_REGISTRY.get(file_type)
    if extractor_cls is None:
        logger.warning("No extractor for type '%s' — falling back to TXT", file_type)
        from app.services.extractors.txt_extractor import TXTExtractor
        extractor_cls = TXTExtractor

    extractor = extractor_cls()
    try:
        doc = extractor.extract(path)
    except Exception as exc:  # noqa: BLE001
        logger.error("Extractor %s crashed on '%s': %s", extractor_cls.__name__, path.name, exc)
        doc = ParsedDocument(
            filename=path.name,
            file_type=file_type,
            text="",
            extraction_method="failed",
            warnings=[f"Extraction failed: {exc}"],
        )

    doc.source_archive = source_archive
    if not doc.sha256:
        try:
            doc.sha256 = compute_sha256(path)
        except OSError as exc:
            doc.warnings.append(f"SHA-256 computation failed: {exc}")

    return doc
