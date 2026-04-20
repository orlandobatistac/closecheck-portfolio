"""
Day 3: Field extraction via Claude.
Given a document type and its text, extracts structured fields defined in FIELDS_BY_DOC_TYPE.
"""
import json

from app.llm.client import claude_json
from app.llm.prompts import FIELD_EXTRACTOR_PROMPT, FIELDS_BY_DOC_TYPE

# Max characters for a single extraction prompt.
# Head+tail sampling preserves both header fields (names, price, date)
# and tail fields (Schedule B exceptions, addendums, signatures).
_SAMPLE_MAX_CHARS = 40_000
_SECTION_OMITTED_MARKER = "\n\n[--- DOCUMENT MIDDLE OMITTED FOR BREVITY ---]\n\n"


def _smart_sample(text: str, max_chars: int = _SAMPLE_MAX_CHARS) -> str:
    """
    Return text unchanged if it fits within max_chars.
    Otherwise return the first half + separator + last half, preserving
    both the document header (names, dates, amounts) and the tail
    (Schedule B exceptions, addendums, signatures).
    """
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + _SECTION_OMITTED_MARKER + text[-half:]


def _prepare_title_text(text: str) -> str:
    """
    For title commitments: use ALTA section detection first.
    Falls back to smart_sample if no section markers are found.
    """
    from app.services.doc_sections import extract_title_sections, build_title_prompt_text
    sections = extract_title_sections(text)
    if sections:
        return build_title_prompt_text(sections)
    return _smart_sample(text)


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

    if document_type == "title_commitment":
        prompt_text = _prepare_title_text(text)
    else:
        prompt_text = _smart_sample(text)

    prompt = FIELD_EXTRACTOR_PROMPT.format(
        fields_json=json.dumps(fields, indent=2),
        text=prompt_text,
    )
    return claude_json(prompt, max_tokens=1024)

