"""Unit + integration tests for PDF report generation — Day 9."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── sample report fixture ─────────────────────────────────────────────────────

_SAMPLE_REPORT = {
    "overall": "WARNING",
    "summary": {"total_rules": 4, "passed": 2, "warnings": 1, "failed": 1},
    "documents": [
        {"filename": "pa.pdf", "document_type": "purchase_agreement",
         "confidence": 0.95, "status": "ok"},
    ],
    "results": [
        {"rule_id": "PA-001", "category": "purchase_agreement",
         "description": "Buyer name consistent", "severity": "FAIL",
         "status": "FAIL", "detail": "Name mismatch", "documents_referenced": []},
        {"rule_id": "PA-003", "category": "purchase_agreement",
         "description": "Purchase price matches", "severity": "WARNING",
         "status": "WARNING", "detail": None, "documents_referenced": []},
        {"rule_id": "PA-005", "category": "purchase_agreement",
         "description": "Earnest money documented", "severity": "WARNING",
         "status": "PASS", "detail": None, "documents_referenced": []},
        {"rule_id": "PA-007", "category": "purchase_agreement",
         "description": "Contingencies noted", "severity": "INFO",
         "status": "PASS", "detail": None, "documents_referenced": []},
    ],
    "conflicts": [
        {"rule_id": "PA-001", "type": "Name mismatch", "severity": "FAIL",
         "message": "Buyer name differs", "resolved": False,
         "field": "buyer_name", "doc_a": "Purchase Agreement",
         "value_a": "Carlos Martinez", "doc_b": "Loan Note",
         "value_b": "Carlos Martínez"},
    ],
    "executive_brief": [
        "Buyer name inconsistency detected across documents.",
        "Purchase price requires verification.",
        "All title commitment checks passed.",
        "Insurance binder not yet submitted.",
        "Closing is on track pending name correction.",
    ],
    "action_plan": [
        {"title": "Fix buyer name", "description": "Correct the name spelling",
         "urgency": "now", "owner": "coordinator", "is_blocker": True},
        {"title": "Verify price", "description": "Confirm purchase price",
         "urgency": "today", "owner": "lender", "is_blocker": False},
    ],
}


# ── unit tests for pdf_generator ─────────────────────────────────────────────

class TestGeneratePdf:
    def test_creates_pdf_file(self):
        from app.services.pdf_generator import generate_pdf
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "test_report.pdf")
            result = generate_pdf(_SAMPLE_REPORT, out, job_id="abcd1234")
            assert Path(result).exists()
            assert Path(result).stat().st_size > 1000  # non-trivial file

    def test_pdf_has_valid_header(self):
        from app.services.pdf_generator import generate_pdf
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "test_report.pdf")
            generate_pdf(_SAMPLE_REPORT, out, job_id="abcd1234")
            with open(out, "rb") as f:
                header = f.read(5)
            assert header == b"%PDF-"

    def test_empty_report_does_not_crash(self):
        from app.services.pdf_generator import generate_pdf
        minimal = {
            "overall": "PASS",
            "summary": {"total_rules": 0, "passed": 0, "warnings": 0, "failed": 0},
            "documents": [],
            "results": [],
            "conflicts": [],
            "executive_brief": [],
            "action_plan": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "empty_report.pdf")
            result = generate_pdf(minimal, out, job_id="00000000")
            assert Path(result).exists()

    def test_fail_triage_does_not_crash(self):
        from app.services.pdf_generator import generate_pdf
        report = dict(_SAMPLE_REPORT, overall="FAIL")
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "fail_report.pdf")
            result = generate_pdf(report, out, job_id="failtest")
            assert Path(result).exists()

    def test_pass_triage_does_not_crash(self):
        from app.services.pdf_generator import generate_pdf
        report = dict(_SAMPLE_REPORT, overall="PASS",
                      conflicts=[], executive_brief=["All clear."], action_plan=[])
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "pass_report.pdf")
            result = generate_pdf(report, out, job_id="passtest")
            assert Path(result).exists()

    def test_creates_parent_dirs(self):
        from app.services.pdf_generator import generate_pdf
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "nested" / "deep" / "report.pdf")
            result = generate_pdf(_SAMPLE_REPORT, out, job_id="nesttest")
            assert Path(result).exists()


# ── integration tests for GET /report/{job_id}/pdf ───────────────────────────

def _make_pdf_bytes() -> bytes:
    return (b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"xref\n0 1\n0000000000 65535 f\n"
            b"trailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n9\n%%EOF")


@pytest.fixture()
def mock_claude():
    with patch("app.llm.client.get_client") as mock_get:
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(
            text='{"document_type": "purchase_agreement", "confidence": 0.92, "notes": ""}'
        )]
        mock_client.messages.create.return_value = mock_message
        mock_get.return_value = mock_client
        yield mock_client


class TestReportPdfEndpoint:
    def test_unknown_job_returns_404(self):
        resp = client.get("/api/v1/report/non-existent-id/pdf")
        assert resp.status_code == 404

    def test_pending_job_returns_409(self, mock_claude):
        # Submit a job but don't wait for completion
        submit = client.post(
            "/api/v1/validate",
            files=[("files", ("pa.pdf", _make_pdf_bytes(), "application/pdf"))],
        )
        assert submit.status_code == 202
        job_id = submit.json()["job_id"]

        # The background task may or may not have run — if pending/processing → 409
        # If completed (fast mock), skip this assertion
        resp = client.get(f"/api/v1/report/{job_id}/pdf")
        if resp.status_code == 409:
            assert "not completed" in resp.json()["detail"].lower()
        else:
            # If the background task ran fast and completed, that's also valid
            assert resp.status_code in (200, 409)

    def test_completed_job_returns_pdf(self, tmp_path, mock_claude):
        """Inject a completed job with a pre-built report and verify the endpoint
        returns 200 with content-type application/pdf."""
        import json
        import uuid
        from datetime import datetime

        from sqlalchemy.orm import Session

        from app.config import settings
        from app.db.database import SessionLocal
        from app.models.job import JobStatus, ValidationJob

        job_id = str(uuid.uuid4())

        # Persist report.json to the uploads dir so load_report works
        job_dir = Path(settings.upload_dir) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "report.json").write_text(
            json.dumps(_SAMPLE_REPORT), encoding="utf-8"
        )

        # Insert a completed job into the DB
        db: Session = SessionLocal()
        try:
            job = ValidationJob(
                id=job_id,
                status=JobStatus.COMPLETED,
                transaction_type="residential",
                file_count=1,
                overall="WARNING",
                completed_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
        finally:
            db.close()

        resp = client.get(f"/api/v1/report/{job_id}/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_pdf_is_cached_on_second_request(self, mock_claude):
        """Second request for the same job should serve the cached file (same content)."""
        import json
        import uuid
        from datetime import datetime

        from app.config import settings
        from app.db.database import SessionLocal
        from app.models.job import JobStatus, ValidationJob

        job_id = str(uuid.uuid4())
        job_dir = Path(settings.upload_dir) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "report.json").write_text(
            json.dumps(_SAMPLE_REPORT), encoding="utf-8"
        )

        db = SessionLocal()
        try:
            job = ValidationJob(
                id=job_id,
                status=JobStatus.COMPLETED,
                transaction_type="residential",
                file_count=1,
                overall="WARNING",
                completed_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
        finally:
            db.close()

        resp1 = client.get(f"/api/v1/report/{job_id}/pdf")
        resp2 = client.get(f"/api/v1/report/{job_id}/pdf")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Both responses should be identical PDFs
        assert resp1.content == resp2.content
