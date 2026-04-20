"""
File text extraction — backward-compatible wrapper around the extractors package.

`extract_text` is kept for compatibility with existing tests and any code that
calls it directly. New code should use `extract_document` from
`app.services.extractors` instead.
"""
from pathlib import Path

from app.services.extractors import extract_document
from app.services.file_type_detector import detect_file_type


def extract_text(file_path: Path) -> str:
    """
    Extract raw text from *file_path* using the appropriate format extractor.

    Raises ValueError if the file type is unknown/unsupported.
    """
    file_type = detect_file_type(file_path)
    if file_type == "unknown":
        raise ValueError(
            f"Unsupported file type for '{file_path.name}'. "
            "Cannot determine format from magic bytes or extension."
        )
    doc = extract_document(file_path, file_type)
    if doc.extraction_method == "failed" and not doc.text:
        # Surface the first warning as an exception to preserve original behavior
        err = doc.warnings[0] if doc.warnings else f"Extraction failed for '{file_path.name}'"
        raise ValueError(err)
    return doc.text


# ── Keep private helpers for any code that might import them directly ─────────

def _extract_pdf(path: Path) -> str:
    from app.services.extractors.pdf_extractor import PDFExtractor
    return PDFExtractor().extract(path).text


def _extract_docx(path: Path) -> str:
    from app.services.extractors.docx_extractor import DOCXExtractor
    return DOCXExtractor().extract(path).text

