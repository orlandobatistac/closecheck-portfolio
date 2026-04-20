"""
Section-aware document parsing utilities.

Provides regex-based section detection for real estate documents that have
predictable structural markers (Title Commitments follow the ALTA standard).
"""
import re
from typing import Optional


# ALTA Title Commitment section header patterns (case-insensitive, varied whitespace).
# Ordered from most generic to most specific within each schedule group.
_SECTION_PATTERNS: list[tuple[str, str]] = [
    # Schedule A — property description, insured amounts, effective date
    (
        "schedule_a",
        r"SCHEDULE\s+A\b",
    ),
    # Schedule B-I / Requirements (must be checked before the generic B pattern)
    (
        "schedule_b1",
        r"SCHEDULE\s+B(?:[,\-\u2013\u2014]\s*(?:SECTION\s+)?(?:I|1)\b|\s+I\b|[\-\u2013\u2014]I\b)"
        r"|REQUIREMENTS?\s+(?:TO\s+TITLE|FOR\s+INSURANCE)",
    ),
    # Schedule B-II / Exceptions — most critical section for lien/exception detection
    (
        "schedule_b2",
        r"SCHEDULE\s+B(?:[,\-\u2013\u2014]\s*(?:SECTION\s+)?(?:II|2)\b|\s+II\b|[\-\u2013\u2014]II\b)"
        r"|EXCEPTIONS?\s+(?:TO\s+(?:TITLE\s+)?COVERAGE|FROM\s+COVERAGE)"
        r"|TITLE\s+EXCEPTIONS?",
    ),
]

# Compiled once on first use
_COMPILED: Optional[list[tuple[str, re.Pattern]]] = None


def _get_compiled() -> list[tuple[str, re.Pattern]]:
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = [
            (name, re.compile(pattern, re.IGNORECASE))
            for name, pattern in _SECTION_PATTERNS
        ]
    return _COMPILED


def extract_title_sections(text: str) -> dict[str, str]:
    """
    Detect ALTA-standard Schedule A / B-I / B-II sections in a Title Commitment.

    Returns a dict with keys "schedule_a", "schedule_b1", "schedule_b2" mapped
    to the text of that section. Only keys whose section was found are included.
    Returns an empty dict if no section markers are detected (caller should fallback
    to smart_sample).

    The text of each section spans from its own header to the start of the
    next detected header (or end of document).
    """
    compiled = _get_compiled()

    # Find the first occurrence of each section marker
    markers: list[tuple[int, str]] = []
    for name, pattern in compiled:
        m = pattern.search(text)
        if m:
            markers.append((m.start(), name))

    if not markers:
        return {}

    # Sort by position in document
    markers.sort(key=lambda x: x[0])

    # Slice text between consecutive markers
    sections: dict[str, str] = {}
    for i, (pos, name) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
        sections[name] = text[pos:end].strip()

    return sections


def build_title_prompt_text(sections: dict[str, str]) -> str:
    """
    Concatenate detected title sections into a compact prompt-ready string.
    Sections are ordered A → B-I → B-II with clear labels.
    """
    parts: list[str] = []
    for key, label in [
        ("schedule_a",  "SCHEDULE A"),
        ("schedule_b1", "SCHEDULE B-I (Requirements)"),
        ("schedule_b2", "SCHEDULE B-II (Exceptions)"),
    ]:
        if key in sections:
            parts.append(f"[{label}]\n{sections[key]}")
    return "\n\n".join(parts)
