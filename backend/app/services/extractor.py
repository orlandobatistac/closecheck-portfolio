"""
Day 3: Field extraction via Claude.
Given a document type and its text, extracts structured fields defined in FIELDS_BY_DOC_TYPE.
"""
import json

from app.llm.client import claude_json
from app.llm.prompts import FIELD_EXTRACTOR_PROMPT, FIELDS_BY_DOC_TYPE


def extract_fields(document_type: str, text: str) -> dict:
    """
    Extract structured fields from document text using Claude.
    Returns a dict mapping field names to extracted values (None if not found).
    Raises ValueError if document_type has no field schema defined.
    """
    fields = FIELDS_BY_DOC_TYPE.get(document_type)
    if not fields:
        raise ValueError(
            f"No field schema defined for document type '{document_type}'. "
            f"Add it to FIELDS_BY_DOC_TYPE in llm/prompts.py before extracting fields."
        )

    prompt = FIELD_EXTRACTOR_PROMPT.format(
        fields_json=json.dumps(fields, indent=2),
        text=text[:12000],
    )
    return claude_json(prompt, max_tokens=1024)

