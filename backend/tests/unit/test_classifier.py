"""Unit tests for document classifier (Day 3)."""
import pytest
from unittest.mock import patch

from app.llm.client import ClaudeResponseError
from app.services.classifier import classify_document, ClassificationResult


def _mock_claude_json(response: dict):
    return patch("app.services.classifier.claude_json", return_value=response)


def test_classify_returns_correct_type():
    with _mock_claude_json({"document_type": "purchase_agreement", "confidence": 0.95, "notes": "Contains buyer/seller"}):
        result = classify_document("some document text")
    assert result.document_type == "purchase_agreement"
    assert result.confidence == 0.95
    assert "buyer" in result.notes


def test_classify_raises_on_empty_response():
    """Empty response must raise ClaudeResponseError — no silent fallback to 'other'."""
    with _mock_claude_json({}):
        with pytest.raises(ClaudeResponseError, match="missing required fields"):
            classify_document("unrecognized document text")


def test_classify_raises_on_unknown_document_type():
    """Unknown document types must raise ClaudeResponseError."""
    with _mock_claude_json({"document_type": "unknown_type", "confidence": 0.9, "notes": ""}):
        with pytest.raises(ClaudeResponseError, match="unknown document type"):
            classify_document("some text")


def test_classify_confidence_cast_to_float():
    with _mock_claude_json({"document_type": "title_commitment", "confidence": "0.88", "notes": ""}):
        result = classify_document("title text")
    assert isinstance(result.confidence, float)
    assert result.confidence == 0.88


def test_classify_prompt_includes_text_snippet():
    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {"document_type": "closing_disclosure", "confidence": 0.9, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        classify_document("closing costs summary for buyer")

    assert "closing costs summary for buyer" in captured["prompt"]


def test_classify_truncates_long_text():
    long_text = "x" * 20000
    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {"document_type": "other", "confidence": 0.5, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        classify_document(long_text)

    assert long_text not in captured["prompt"]

