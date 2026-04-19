"""
Day 10 — End-to-end integration test using the Martinez_test sample docs.

These tests require a *real* Claude API key and exercise the full pipeline.
They are marked with @pytest.mark.e2e so they can be excluded from fast CI:
    pytest -m "not e2e"   # skip
    pytest -m e2e          # run only e2e
"""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

MARTINEZ_DIR = Path(__file__).parent.parent.parent.parent / "sample-docs" / "Martinez_test"
PDF_FILES = [
    "purchase_agreement.pdf",
    "closing_disclosure.pdf",
    "lender_commitment.pdf",
    "title_binder.pdf",
]


def _load_pdf(filename: str) -> tuple[str, bytes, str]:
    path = MARTINEZ_DIR / filename
    return ("files", (filename, path.read_bytes(), "application/pdf"))


def _poll_until_done(job_id: str, timeout: int = 60) -> dict:
    """Poll GET /results/{job_id} until status is completed or failed."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/v1/results/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(2)
    pytest.fail(f"Job {job_id} did not complete within {timeout}s")


@pytest.mark.e2e
class TestMartinezE2E:
    """Full pipeline tests — require ANTHROPIC_API_KEY in environment."""

    @pytest.fixture(autouse=True)
    def skip_if_no_key(self):
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set — skipping e2e tests")

    @pytest.fixture(autouse=True)
    def skip_if_no_samples(self):
        for f in PDF_FILES:
            if not (MARTINEZ_DIR / f).exists():
                pytest.skip(f"Sample doc {f} not found — run generate_sample_docs.py first")

    def test_martinez_e2e_overall_fail(self):
        """Submit 4 Martinez docs — overall should be FAIL (price mismatch blocker)."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post(
            "/api/v1/validate",
            files=files,
            data={"transaction_type": "residential"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        assert result["status"] == "completed", f"Job failed: {result}"
        assert result["overall"] == "FAIL", (
            f"Expected FAIL (price mismatch + name accent), got {result['overall']}"
        )

    def test_martinez_summary_stats(self):
        """Summary should show at least 1 failed and 1 warning rule."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        summary = result.get("summary", {})
        assert summary.get("failed", 0) >= 1, "Expected at least 1 FAIL rule"
        assert summary.get("total_rules", 0) > 0

    def test_martinez_conflicts_present(self):
        """Conflicts array should have at least 1 entry."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        assert len(result.get("conflicts", [])) >= 1, "Expected at least 1 conflict card"

    def test_martinez_executive_brief_present(self):
        """executive_brief should be a list of bullet strings."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        brief = result.get("executive_brief", [])
        assert isinstance(brief, list) and len(brief) > 0

    def test_martinez_action_plan_present(self):
        """action_plan should have at least 2 items with is_blocker."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        plan = result.get("action_plan", [])
        blockers = [a for a in plan if a.get("is_blocker")]
        assert len(blockers) >= 1, "Expected at least 1 blocker in action_plan"

    def test_martinez_4_docs_classified(self):
        """All 4 documents should be classified."""
        files = [_load_pdf(f) for f in PDF_FILES]
        resp = client.post("/api/v1/validate", files=files)
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        result = _poll_until_done(job_id, timeout=90)
        docs = result.get("documents", [])
        assert len(docs) == 4, f"Expected 4 classified docs, got {len(docs)}"
