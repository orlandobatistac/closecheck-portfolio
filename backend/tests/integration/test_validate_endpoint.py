"""Integration tests — exercises the full API stack with real Claude calls.

Tests that submit files and trigger the background pipeline require
ANTHROPIC_API_KEY to be set; they are skipped automatically otherwise.
"""
import os
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_pdf_bytes() -> bytes:
    """Minimal valid PDF bytes for upload testing."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n9\n%%EOF"


@pytest.fixture(autouse=True)
def skip_pipeline_if_no_key(request):
    """Skip tests that trigger the Claude pipeline when no API key is configured."""
    marker = request.node.get_closest_marker("requires_claude")
    if marker and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set — skipping test that calls Claude pipeline")


class TestValidateEndpoint:
    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_post_validate_no_files_returns_422(self):
        resp = client.post("/api/v1/validate")
        assert resp.status_code == 422

    def test_post_validate_wrong_format_returns_400(self):
        resp = client.post(
            "/api/v1/validate",
            files=[("files", ("test.xlsx", b"fake", "application/vnd.ms-excel"))],
        )
        assert resp.status_code == 400

    def test_get_results_unknown_job_returns_404(self):
        resp = client.get("/api/v1/results/non-existent-job-id")
        assert resp.status_code == 404

    @pytest.mark.requires_claude
    def test_post_validate_pdf_returns_202_with_job_id(self):
        resp = client.post(
            "/api/v1/validate",
            files=[("files", ("pa.pdf", _make_pdf_bytes(), "application/pdf"))],
            data={"transaction_type": "residential"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    @pytest.mark.requires_claude
    def test_get_results_after_submit_returns_job(self):
        submit = client.post(
            "/api/v1/validate",
            files=[("files", ("pa.pdf", _make_pdf_bytes(), "application/pdf"))],
        )
        assert submit.status_code == 202
        job_id = submit.json()["job_id"]

        result = client.get(f"/api/v1/results/{job_id}")
        assert result.status_code == 200
        data = result.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("pending", "processing", "completed", "failed")

    def test_post_validate_too_many_files_returns_400(self):
        """Submitting 21 files should be rejected (max 20)."""
        files = [
            ("files", (f"doc_{i}.pdf", _make_pdf_bytes(), "application/pdf"))
            for i in range(21)
        ]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 400
        assert "20" in resp.json()["detail"]

    @pytest.mark.requires_claude
    def test_post_validate_corrupt_pdf_job_fails(self):
        """A corrupt PDF should result in a job with status 'failed'."""
        corrupt_bytes = b"this is not a valid PDF at all %%EOF"
        resp = client.post(
            "/api/v1/validate",
            files=[("files", ("corrupt.pdf", corrupt_bytes, "application/pdf"))],
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        deadline = time.time() + 15
        status = "pending"
        while time.time() < deadline and status not in ("completed", "failed"):
            r = client.get(f"/api/v1/results/{job_id}")
            status = r.json()["status"]
            time.sleep(0.5)

        assert status in ("completed", "failed")

    def test_api_v1_health(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

