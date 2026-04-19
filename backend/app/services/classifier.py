"""
Day 3: Document type classification via Claude.
Given extracted text, returns the document category and confidence score.
"""
from dataclasses import dataclass

from app.llm.client import ClaudeResponseError, claude_json
from app.llm.prompts import CLASSIFIER_PROMPT


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


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    notes: str = ""


def classify_document(text: str) -> ClassificationResult:
    """Use Claude to classify a document into one of the known real estate types."""
    prompt = CLASSIFIER_PROMPT.format(
        document_types=", ".join(DOCUMENT_TYPES),
        text=text[:8000],
    )
    result = claude_json(prompt)

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
    )

