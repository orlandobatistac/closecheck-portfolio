"""
Day 3: Document type classification via Claude.
Given extracted text, returns the document category and confidence score.

Uses a cascade strategy: fast/cheap Haiku model first; escalates to Sonnet
only when confidence is below the threshold (ambiguous document types).
"""
import logging
from dataclasses import dataclass, field

from app.llm.client import ClaudeResponseError, claude_json
from app.llm.prompts import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = [
    "purchase_agreement",
    "title_commitment",
    "closing_disclosure",
    "hud1",
    "loan_note",
    "mortgage_deed",
    "insurance_binder",
    "survey",
    "hoa_document",
    "tax_certificate",
    "id_document",
    "wire_instructions",
    "other",
]

# Confidence threshold: Haiku results at or above this are accepted as-is.
# Below it, the call is escalated to Sonnet for ambiguous document types.
_HAIKU_CONFIDENCE_THRESHOLD = 0.85

# Characters sent to the classifier — more than before (was 8000) so the
# classifier sees a fuller picture of the document.
_CLASSIFY_MAX_CHARS = 12_000


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    notes: str = ""
    model_used: str = field(default="", compare=False)


def classify_document(text: str) -> ClassificationResult:
    """
    Classify a document using a Haiku → Sonnet cascade:
      1. Try claude-haiku (fast, cheap).
      2. If confidence >= 0.85, accept the result immediately.
      3. Otherwise escalate to the primary Sonnet model for ambiguous cases
         (hud1 vs closing_disclosure, mortgage_deed vs loan_note, etc.).
    """
    from app.config import settings

    haiku_result = _call_classifier(text, model=settings.claude_haiku_model)
    if haiku_result.confidence >= _HAIKU_CONFIDENCE_THRESHOLD:
        logger.debug(
            "Classifier: haiku → %s (confidence=%.2f) ✓",
            haiku_result.document_type, haiku_result.confidence,
        )
        return haiku_result

    logger.info(
        "Classifier: haiku low confidence %.2f for '%s' — escalating to sonnet",
        haiku_result.confidence, haiku_result.document_type,
    )
    sonnet_result = _call_classifier(text, model=settings.claude_model)
    logger.debug(
        "Classifier: sonnet → %s (confidence=%.2f)",
        sonnet_result.document_type, sonnet_result.confidence,
    )
    return sonnet_result


def _call_classifier(text: str, model: str) -> ClassificationResult:
    """Send a classification prompt to the specified model and parse the result."""
    prompt = CLASSIFIER_PROMPT.format(
        document_types=", ".join(DOCUMENT_TYPES),
        text=text[:_CLASSIFY_MAX_CHARS],
    )
    result = claude_json(prompt, model=model)

    doc_type = result.get("document_type")
    confidence = result.get("confidence")
    if not doc_type or confidence is None:
        raise ClaudeResponseError(
            f"Claude classifier response is missing required fields 'document_type' or 'confidence'. "
            f"Got: {result!r}. Ensure the classifier prompt instructs Claude to return both fields."
        )
    if doc_type not in DOCUMENT_TYPES:
        raise ClaudeResponseError(
            f"Claude returned an unknown document type '{doc_type}'. "
            f"Expected one of: {', '.join(DOCUMENT_TYPES)}."
        )

    return ClassificationResult(
        document_type=doc_type,
        confidence=float(confidence),
        notes=result.get("notes", ""),
        model_used=model,
    )

