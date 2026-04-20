"""
PDF extractor — native text first, OCR via Claude Vision for scanned pages.
"""
import io
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

# If average chars per page is below this threshold, the PDF is likely scanned.
_NATIVE_CHARS_PER_PAGE_THRESHOLD = 20


class PDFExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        warnings: list[str] = []

        try:
            import fitz  # PyMuPDF
        except ImportError:
            return ParsedDocument(
                filename=path.name,
                file_type="pdf",
                text="",
                extraction_method="failed",
                warnings=["PyMuPDF is not installed."],
                sha256=compute_sha256(path),
            )

        try:
            doc = fitz.open(str(path))
        except fitz.EmptyFileError:
            return ParsedDocument(
                filename=path.name,
                file_type="pdf",
                text="",
                extraction_method="failed",
                warnings=["Empty or corrupt PDF — file could not be opened."],
                sha256=compute_sha256(path),
            )
        except Exception as exc:  # noqa: BLE001
            return ParsedDocument(
                filename=path.name,
                file_type="pdf",
                text="",
                extraction_method="failed",
                warnings=[f"PDF open error: {exc}"],
                sha256=compute_sha256(path),
            )

        page_count = len(doc)
        native_texts: list[str] = []

        for page in doc:
            native_texts.append(page.get_text())

        doc.close()

        total_chars = sum(len(t) for t in native_texts)
        avg_chars = total_chars / max(page_count, 1)

        if avg_chars >= _NATIVE_CHARS_PER_PAGE_THRESHOLD:
            # Native text is sufficient
            text = "\n".join(native_texts)
            method = "native"
        else:
            # Scanned PDF — fall back to Claude Vision page by page
            logger.info(
                "'%s' looks scanned (avg %.1f chars/page). Using OCR via Claude Vision.",
                path.name,
                avg_chars,
            )
            text, method, ocr_warnings = _ocr_pdf(path)
            warnings.extend(ocr_warnings)

        return ParsedDocument(
            filename=path.name,
            file_type="pdf",
            text=text.strip(),
            metadata={"pages": page_count, "avg_chars_per_page": round(avg_chars, 1)},
            extraction_method=method,
            warnings=warnings,
            sha256=compute_sha256(path),
        )


def _ocr_pdf(path: Path) -> tuple[str, str, list[str]]:
    """Render each page as PNG and send to Claude Vision. Returns (text, method, warnings)."""
    warnings: list[str] = []
    pages_text: list[str] = []

    try:
        import fitz
        from app.llm.vision import claude_vision

        doc = fitz.open(str(path))
        for i, page in enumerate(doc):
            try:
                mat = fitz.Matrix(2, 2)  # 2× zoom = ~144 dpi
                pix = page.get_pixmap(matrix=mat)
                png_bytes = pix.tobytes("png")
                page_text = claude_vision(png_bytes, mime_type="image/png")
                pages_text.append(page_text)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"OCR failed for page {i + 1}: {exc}")
                pages_text.append("")
        doc.close()

    except Exception as exc:  # noqa: BLE001
        warnings.append(f"OCR pipeline error: {exc}")
        return "", "ocr-failed", warnings

    return "\n\n".join(pages_text), "ocr-vision", warnings
