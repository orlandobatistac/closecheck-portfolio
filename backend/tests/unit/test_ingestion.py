"""Unit tests for ingestion helpers (Day 2)."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def test_save_and_load_extracted_texts(tmp_path):
    from app.services.ingestion import save_extracted_texts, load_extracted_texts

    texts = {"purchase.pdf": "Buyer: Jane Doe", "title.docx": "Legal description: Lot 1"}

    with patch("app.services.ingestion.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        job_id = "test-job-123"
        (tmp_path / job_id).mkdir()

        save_extracted_texts(job_id, texts)
        loaded = load_extracted_texts(job_id)

    assert loaded == texts


def test_load_extracted_texts_missing_job(tmp_path):
    from app.services.ingestion import load_extracted_texts

    with patch("app.services.ingestion.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        result = load_extracted_texts("nonexistent-job")

    assert result == {}


def test_save_uploaded_files(tmp_path):
    from app.services.ingestion import save_uploaded_files

    payloads = [("doc1.pdf", b"%PDF-1.4 fake"), ("doc2.docx", b"PK fake")]

    with patch("app.services.ingestion.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        saved = save_uploaded_files("job-abc", payloads)

    assert len(saved) == 2
    assert all(p.exists() for p in saved)
    assert saved[0].read_bytes() == b"%PDF-1.4 fake"
