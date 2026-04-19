"""
Day 2: File text extraction.
Supports PDF (via PyMuPDF) and DOCX (via python-docx).
"""
from pathlib import Path

import fitz  # PyMuPDF


def extract_text(file_path: Path) -> str:
    """Extract raw text from a PDF or DOCX file."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(path: Path) -> str:
    try:
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except fitz.EmptyFileError:
        raise ValueError(
            f"Cannot extract text from '{path.name}': the file is empty. "
            f"Please upload a valid PDF document."
        )
    except fitz.FileDataError:
        raise ValueError(
            f"Cannot extract text from '{path.name}': the file is corrupted or not a valid PDF. "
            f"Please verify the file can be opened in a PDF viewer before uploading."
        )


def _extract_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

