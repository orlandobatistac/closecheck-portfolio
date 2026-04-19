"""Unit tests for field extractor (Day 3)."""
import pytest
from unittest.mock import patch

from app.services.extractor import extract_fields


def _mock_claude_json(response: dict):
    return patch("app.services.extractor.claude_json", return_value=response)


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


def test_extract_truncates_long_text():
    long_text = "y" * 20000
    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {}

    with patch("app.services.extractor.claude_json", side_effect=fake_claude_json):
        extract_fields("title_commitment", long_text)

    assert long_text not in captured["prompt"]

