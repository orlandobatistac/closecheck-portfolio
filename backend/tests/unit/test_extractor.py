"""Unit tests for field extractor (Day 3)."""
import pytest
from unittest.mock import patch

from app.services.extractor import extract_fields, _smart_sample, _SAMPLE_MAX_CHARS, _SECTION_OMITTED_MARKER


def _mock_claude_json(response: dict):
    return patch("app.services.extractor.claude_json", return_value=response)


# ── existing tests (unchanged behaviour) ──────────────────────────────────────

def test_extract_known_doc_type():
    expected = {"buyer_name": "John Smith", "seller_name": "Jane Doe", "purchase_price": "500000"}
    with _mock_claude_json(expected):
        result = extract_fields("purchase_agreement", "some text")
    assert result["buyer_name"] == "John Smith"
    assert result["purchase_price"] == "500000"


def test_extract_unknown_doc_type_raises():
    """Unknown document types must raise ValueError — no silent empty return."""
    with pytest.raises(ValueError, match="No field schema defined for document type 'unknown_type'"):
        extract_fields("unknown_type", "some text")


def test_extract_other_doc_type_raises():
    """'other' has no schema — must raise ValueError."""
    with pytest.raises(ValueError, match="No field schema defined for document type 'other'"):
        extract_fields("other", "some text")


def test_extract_null_fields_preserved():
    response = {"cash_to_close": None, "seller_credits": "5000", "prorated_taxes": None, "total_closing_costs": "12000", "lender_fees": None}
    with _mock_claude_json(response):
        result = extract_fields("closing_disclosure", "some text")
    assert result["cash_to_close"] is None
    assert result["seller_credits"] == "5000"


def test_extract_prompt_includes_fields_schema():
    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    with patch("app.services.extractor.claude_json", side_effect=fake_claude_json):
        extract_fields("loan_note", "loan document text")

    assert "borrower_name" in captured["prompt"]
    assert "loan_amount" in captured["prompt"]
    assert "interest_rate" in captured["prompt"]


# ── _smart_sample unit tests ───────────────────────────────────────────────────

def test_smart_sample_passthrough_for_short_text():
    """Text shorter than max_chars is returned unchanged."""
    text = "short document text"
    assert _smart_sample(text) is text


def test_smart_sample_passthrough_at_exact_limit():
    text = "x" * _SAMPLE_MAX_CHARS
    assert _smart_sample(text) is text


def test_smart_sample_preserves_head_and_tail():
    """For long documents, both the first and last characters survive sampling."""
    head = "HEAD_" * 100          # 500 chars
    tail = "_TAIL" * 100          # 500 chars
    middle = "M" * 80_000         # far exceeds limit
    long_text = head + middle + tail

    sampled = _smart_sample(long_text)

    assert len(sampled) <= _SAMPLE_MAX_CHARS + len(_SECTION_OMITTED_MARKER)
    assert sampled.startswith(head)
    assert sampled.endswith(tail)
    assert _SECTION_OMITTED_MARKER in sampled


def test_smart_sample_original_not_in_result_when_long():
    """The full original string must NOT appear in the sampled result."""
    long_text = "y" * (_SAMPLE_MAX_CHARS * 2)
    sampled = _smart_sample(long_text)
    assert long_text not in sampled


# ── extract_fields: long text uses smart_sample, not blind truncation ──────────

def test_extract_smart_samples_long_text():
    """Long text: the head AND tail of the document reach Claude's prompt."""
    head = "HEADER_INFO_" * 200    # ~2400 chars
    tail = "SCHEDULE_B_" * 2000    # ~22000 chars at end
    long_text = head + "M" * 60_000 + tail

    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    with patch("app.services.extractor.claude_json", side_effect=fake_claude_json):
        extract_fields("title_commitment", long_text)

    # Both ends must be present — the old [:12000] would have lost the tail
    assert "HEADER_INFO_" in captured["prompt"]
    assert "SCHEDULE_B_" in captured["prompt"]


# ── extract_fields: title_commitment uses section-aware path ───────────────────

def test_extract_title_commitment_uses_sections_when_detected():
    """When ALTA section markers are found, the structured sections reach Claude."""
    title_text = (
        "SCHEDULE A\nEffective Date: 04/01/2026\nInsurance Amount: $485,000\n\n"
        "SCHEDULE B-I\nRequirement: Pay off existing mortgage\n\n"
        "SCHEDULE B-II\nException 1: Easement for utilities\nException 2: HOA covenants\n"
    )

    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    with patch("app.services.extractor.claude_json", side_effect=fake_claude_json):
        extract_fields("title_commitment", title_text)

    assert "SCHEDULE A" in captured["prompt"]
    assert "SCHEDULE B-II" in captured["prompt"]
    assert "Easement for utilities" in captured["prompt"]
    # Section labels should be present
    assert "Exceptions" in captured["prompt"]


def test_extract_title_commitment_fallback_on_no_sections():
    """Without ALTA markers, title_commitment falls back to smart_sample."""
    plain_text = "A" * 50_000  # long, no section markers

    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    with patch("app.services.extractor.claude_json", side_effect=fake_claude_json):
        extract_fields("title_commitment", plain_text)

    # Should have used smart_sample — marker present, full text absent
    assert _SECTION_OMITTED_MARKER in captured["prompt"]
    assert plain_text not in captured["prompt"]

