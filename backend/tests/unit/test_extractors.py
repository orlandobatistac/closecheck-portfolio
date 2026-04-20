"""
Unit tests for format extractors.
Each test creates a minimal valid file in tmp_path and verifies:
  - text is non-empty (or has an expected warning)
  - file_type is correct
  - sha256 is populated
"""
import csv
import io
import json
import zipfile
from pathlib import Path

import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

def _png_bytes() -> bytes:
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )


def _make_docx(text: str, tmp_path: Path) -> Path:
    from docx import Document
    doc = Document()
    doc.add_paragraph(text)
    dest = tmp_path / "sample.docx"
    doc.save(str(dest))
    return dest


def _make_xlsx(data: list[list], tmp_path: Path) -> Path:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for row in data:
        ws.append(row)
    dest = tmp_path / "sample.xlsx"
    wb.save(str(dest))
    return dest


# ── TXT ────────────────────────────────────────────────────────────────────────

def test_txt_extractor_utf8(tmp_path: Path):
    from app.services.extractors.txt_extractor import TXTExtractor
    p = tmp_path / "notes.txt"
    p.write_bytes("Hello world".encode("utf-8"))
    doc = TXTExtractor().extract(p)
    assert doc.file_type == "txt"
    assert "Hello world" in doc.text
    assert doc.sha256 != ""


def test_txt_extractor_latin1(tmp_path: Path):
    from app.services.extractors.txt_extractor import TXTExtractor
    p = tmp_path / "latin.txt"
    p.write_bytes("caf\xe9".encode("latin-1"))  # 'café'
    doc = TXTExtractor().extract(p)
    assert "caf" in doc.text


# ── JSON ───────────────────────────────────────────────────────────────────────

def test_json_extractor_dict(tmp_path: Path):
    from app.services.extractors.json_extractor import JSONExtractor
    p = tmp_path / "data.json"
    p.write_text(json.dumps({"key": "value", "num": 42}), encoding="utf-8")
    doc = JSONExtractor().extract(p)
    assert doc.file_type == "json"
    assert "key" in doc.text
    assert doc.metadata["root_type"] == "dict"


def test_json_extractor_list_truncated(tmp_path: Path):
    from app.services.extractors.json_extractor import JSONExtractor
    big_list = [{"id": i, "val": f"item{i}"} for i in range(50)]
    p = tmp_path / "big.json"
    p.write_text(json.dumps(big_list), encoding="utf-8")
    doc = JSONExtractor().extract(p)
    assert doc.metadata["item_count"] == 50
    assert any("10" in w for w in doc.warnings)


def test_json_extractor_invalid(tmp_path: Path):
    from app.services.extractors.json_extractor import JSONExtractor
    p = tmp_path / "bad.json"
    p.write_bytes(b"{not valid json!!")
    doc = JSONExtractor().extract(p)
    assert doc.extraction_method == "raw"
    assert len(doc.warnings) > 0


# ── CSV ────────────────────────────────────────────────────────────────────────

def test_csv_extractor(tmp_path: Path):
    from app.services.extractors.csv_extractor import CSVExtractor
    p = tmp_path / "data.csv"
    p.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")
    doc = CSVExtractor().extract(p)
    assert doc.file_type == "csv"
    assert "Alice" in doc.text
    assert doc.metadata["row_count"] == 3


def test_csv_extractor_semicolon_delimiter(tmp_path: Path):
    from app.services.extractors.csv_extractor import CSVExtractor
    p = tmp_path / "euro.csv"
    p.write_text("name;value\nfoo;1\nbar;2", encoding="utf-8")
    doc = CSVExtractor().extract(p)
    assert "foo" in doc.text


# ── HTML ───────────────────────────────────────────────────────────────────────

def test_html_extractor(tmp_path: Path):
    from app.services.extractors.html_extractor import HTMLExtractor
    p = tmp_path / "page.html"
    p.write_bytes(
        b"<html><head><title>Test</title><script>alert(1)</script></head>"
        b"<body><p>Hello from HTML</p></body></html>"
    )
    doc = HTMLExtractor().extract(p)
    assert doc.file_type == "html"
    assert "Hello from HTML" in doc.text
    assert "alert" not in doc.text  # script stripped
    assert doc.metadata.get("title") == "Test"


# ── XLSX ───────────────────────────────────────────────────────────────────────

def test_xlsx_extractor(tmp_path: Path):
    from app.services.extractors.xlsx_extractor import XLSXExtractor
    p = _make_xlsx([["Name", "Score"], ["Alice", 95], ["Bob", 87]], tmp_path)
    doc = XLSXExtractor().extract(p)
    assert doc.file_type == "xlsx"
    assert "Alice" in doc.text
    assert "Sheet1" in doc.metadata["sheets"]


def test_xlsx_extractor_corrupt(tmp_path: Path):
    from app.services.extractors.xlsx_extractor import XLSXExtractor
    p = tmp_path / "bad.xlsx"
    p.write_bytes(b"not an xlsx file")
    doc = XLSXExtractor().extract(p)
    assert doc.extraction_method == "failed"
    assert len(doc.warnings) > 0


# ── DOCX ───────────────────────────────────────────────────────────────────────

def test_docx_extractor(tmp_path: Path):
    from app.services.extractors.docx_extractor import DOCXExtractor
    p = _make_docx("Closing date is March 15, 2026", tmp_path)
    doc = DOCXExtractor().extract(p)
    assert doc.file_type == "docx"
    assert "Closing date" in doc.text
    assert doc.metadata["paragraph_count"] >= 1


def test_docx_extractor_corrupt(tmp_path: Path):
    from app.services.extractors.docx_extractor import DOCXExtractor
    p = tmp_path / "bad.docx"
    p.write_bytes(b"definitely not a docx")
    doc = DOCXExtractor().extract(p)
    assert doc.extraction_method == "failed"
    assert len(doc.warnings) > 0


# ── PDF (native only — no OCR needed for native PDFs) ─────────────────────────

def test_pdf_extractor_native(tmp_path: Path):
    from app.services.extractors.pdf_extractor import PDFExtractor

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as rl_canvas
        dest = tmp_path / "sample.pdf"
        c = rl_canvas.Canvas(str(dest), pagesize=letter)
        c.drawString(72, 700, "Purchase Price: $500,000")
        c.save()
    except ImportError:
        pytest.skip("reportlab not available")

    doc = PDFExtractor().extract(dest)
    assert doc.file_type == "pdf"
    assert "500,000" in doc.text
    assert doc.extraction_method == "native"


def test_pdf_extractor_corrupt(tmp_path: Path):
    from app.services.extractors.pdf_extractor import PDFExtractor
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"%PDF-1.4 corrupt bytes \x00\x01")
    doc = PDFExtractor().extract(p)
    assert doc.extraction_method == "failed"
    assert len(doc.warnings) > 0


# ── extract_document router ────────────────────────────────────────────────────

def test_extract_document_routes_txt(tmp_path: Path):
    from app.services.extractors import extract_document
    p = tmp_path / "hello.txt"
    p.write_text("routed correctly", encoding="utf-8")
    doc = extract_document(p, "txt")
    assert "routed correctly" in doc.text
    assert doc.file_type == "txt"
    assert doc.sha256 != ""


def test_extract_document_unknown_falls_back_to_txt(tmp_path: Path):
    from app.services.extractors import extract_document
    p = tmp_path / "mystery.xyz"
    p.write_bytes(b"some plain text content")
    doc = extract_document(p, "unknown_type")
    # falls back to TXTExtractor
    assert "some plain text content" in doc.text
