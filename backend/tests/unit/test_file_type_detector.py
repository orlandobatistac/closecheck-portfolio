"""Unit tests for file_type_detector."""
import zipfile
from pathlib import Path

import pytest


def _write(tmp_path: Path, name: str, content: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


# ── Helpers to create minimal valid files ─────────────────────────────────────

def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%EOF"


def _zip_bytes(tmp_path: Path) -> bytes:
    buf = tmp_path / "_inner.zip"
    with zipfile.ZipFile(str(buf), "w") as zf:
        zf.writestr("hello.txt", "hello")
    return buf.read_bytes()


def _png_bytes() -> bytes:
    # Minimal 1×1 PNG
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_detect_pdf_by_magic(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "doc.pdf", _pdf_bytes())
    assert detect_file_type(p) == "pdf"


def test_detect_pdf_by_extension_fallback(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    # Content is not a real PDF, but extension should fallback
    p = _write(tmp_path, "doc.pdf", b"not a real pdf content here 123")
    result = detect_file_type(p)
    # extension fallback kicks in since magic fails
    assert result == "pdf"


def test_detect_zip_by_magic(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "archive.zip", _zip_bytes(tmp_path))
    assert detect_file_type(p) == "zip"


def test_detect_zip_by_header(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    # Raw PK signature without .zip extension
    p = _write(tmp_path, "noext", _zip_bytes(tmp_path))
    assert detect_file_type(p) == "zip"


def test_detect_image_png(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "img.png", _png_bytes())
    assert detect_file_type(p) == "image"


def test_detect_csv_by_extension(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "data.csv", b"a,b,c\n1,2,3")
    assert detect_file_type(p) == "csv"


def test_detect_json_by_extension(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "data.json", b'{"key": "value"}')
    assert detect_file_type(p) == "json"


def test_detect_txt_by_extension(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "notes.txt", b"hello world")
    assert detect_file_type(p) == "txt"


def test_detect_html_by_extension(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "page.html", b"<html><body>hi</body></html>")
    assert detect_file_type(p) == "html"


def test_detect_unknown(tmp_path: Path):
    from app.services.file_type_detector import detect_file_type
    p = _write(tmp_path, "mystery.xyz123", b"\x00\x01\x02\x03 random binary")
    assert detect_file_type(p) == "unknown"
