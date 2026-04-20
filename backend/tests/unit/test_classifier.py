"""Unit tests for document classifier (Day 3)."""
import pytest
from unittest.mock import patch, call

from app.llm.client import ClaudeResponseError
from app.services.classifier import (
    classify_document, ClassificationResult,
    _call_classifier, _HAIKU_CONFIDENCE_THRESHOLD, _CLASSIFY_MAX_CHARS,
)


def _mock_claude_json(response: dict):
    """Patch claude_json in the classifier module; high-confidence so Haiku returns early."""
    return patch("app.services.classifier.claude_json", return_value=response)


# ── existing tests (unchanged behaviour) ──────────────────────────────────────

def test_classify_returns_correct_type():
    # confidence 0.95 ≥ threshold → Haiku result returned immediately
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
    # 0.88 ≥ 0.85 threshold → returns from Haiku
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


def test_classify_limits_long_text():
    """Classifier must not send the full raw text — limit is _CLASSIFY_MAX_CHARS."""
    long_text = "x" * (_CLASSIFY_MAX_CHARS * 2)
    captured = {}
    def fake_claude_json(prompt, **kwargs):
        captured["prompt"] = prompt
        return {"document_type": "other", "confidence": 0.95, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        classify_document(long_text)

    assert long_text not in captured["prompt"]


# ── cascade behaviour ─────────────────────────────────────────────────────────

def test_classify_uses_haiku_only_on_high_confidence():
    """When Haiku confidence >= threshold, Sonnet must NOT be called."""
    call_count = {"n": 0}
    def fake_claude_json(prompt, model=None, **kwargs):
        call_count["n"] += 1
        return {"document_type": "purchase_agreement", "confidence": 0.95, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        result = classify_document("some document")

    assert call_count["n"] == 1, "Sonnet must not be called when Haiku confidence is high"
    assert result.document_type == "purchase_agreement"


def test_classify_falls_back_to_sonnet_on_low_confidence():
    """When Haiku confidence < threshold, Sonnet must be called and its result returned."""
    from app.config import settings
    responses = [
        # Haiku call — low confidence
        {"document_type": "hud1",              "confidence": 0.65, "notes": "ambiguous"},
        # Sonnet call — high confidence, correct answer
        {"document_type": "closing_disclosure", "confidence": 0.94, "notes": "CFPB form"},
    ]
    call_models = []
    def fake_claude_json(prompt, model=None, **kwargs):
        call_models.append(model)
        return responses[len(call_models) - 1]

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        result = classify_document("closing disclosure document")

    assert len(call_models) == 2, "Both Haiku and Sonnet must be called"
    assert call_models[0] == settings.claude_haiku_model
    assert call_models[1] == settings.claude_model
    assert result.document_type == "closing_disclosure"
    assert result.confidence == 0.94


def test_classify_threshold_boundary_exactly_at_threshold():
    """Confidence exactly equal to threshold must be accepted by Haiku (>= not >)."""
    call_count = {"n": 0}
    def fake_claude_json(prompt, model=None, **kwargs):
        call_count["n"] += 1
        return {"document_type": "loan_note", "confidence": _HAIKU_CONFIDENCE_THRESHOLD, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        result = classify_document("promissory note text")

    assert call_count["n"] == 1
    assert result.document_type == "loan_note"


def test_classify_model_used_field_reflects_actual_model():
    """model_used on the result must identify which model answered."""
    from app.config import settings
    def fake_claude_json(prompt, model=None, **kwargs):
        return {"document_type": "insurance_binder", "confidence": 0.92, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        result = classify_document("insurance certificate text")

    assert result.model_used == settings.claude_haiku_model


# ── _call_classifier unit tests ──────────────────────────────────────────────

def test_call_classifier_passes_model_to_claude_json():
    """_call_classifier must forward its model argument to claude_json."""
    captured = {}
    def fake_claude_json(prompt, model=None, **kwargs):
        captured["model"] = model
        return {"document_type": "survey", "confidence": 0.9, "notes": ""}

    with patch("app.services.classifier.claude_json", side_effect=fake_claude_json):
        result = _call_classifier("survey document", model="custom-model-id")

    assert captured["model"] == "custom-model-id"
    assert result.model_used == "custom-model-id"

