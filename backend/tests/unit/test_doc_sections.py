"""Unit tests for section-aware title commitment parsing (doc_sections.py)."""
import pytest

from app.services.doc_sections import extract_title_sections, build_title_prompt_text


# ── extract_title_sections ─────────────────────────────────────────────────────

def test_detects_standard_schedule_markers():
    text = (
        "SCHEDULE A\n"
        "Effective Date: April 1, 2026\n"
        "Insurance Amount: $485,000\n\n"
        "SCHEDULE B-I\n"
        "Requirements: Pay off first mortgage\n\n"
        "SCHEDULE B-II\n"
        "Exception 1: Easement for utilities along north boundary\n"
        "Exception 2: HOA covenants recorded in Book 1234\n"
    )
    sections = extract_title_sections(text)

    assert "schedule_a" in sections
    assert "schedule_b1" in sections
    assert "schedule_b2" in sections
    assert "Effective Date" in sections["schedule_a"]
    assert "Pay off first mortgage" in sections["schedule_b1"]
    assert "Easement for utilities" in sections["schedule_b2"]


def test_returns_empty_on_no_markers():
    """Documents with no ALTA markers should return empty dict so caller falls back."""
    plain_text = "This is a plain document without any schedule markers."
    assert extract_title_sections(plain_text) == {}


def test_handles_schedule_b_dash_ii_variant():
    """SCHEDULE B-II with em-dash or en-dash variants must be recognised."""
    text = "SCHEDULE A\nPreamble\n\nSCHEDULE B\u2013II\nException: some lien\n"
    sections = extract_title_sections(text)
    assert "schedule_b2" in sections
    assert "some lien" in sections["schedule_b2"]


def test_handles_schedule_b_section_2_variant():
    """'SCHEDULE B, SECTION 2' variant must be recognised as schedule_b2."""
    text = "SCHEDULE A\nPreamble\n\nSCHEDULE B, SECTION 2\nException: another lien\n"
    sections = extract_title_sections(text)
    assert "schedule_b2" in sections


def test_handles_exceptions_to_title_variant():
    """'EXCEPTIONS TO TITLE COVERAGE' variant must be recognised as schedule_b2."""
    text = "SCHEDULE A\nPreamble\n\nEXCEPTIONS TO TITLE COVERAGE\nSome exceptions here\n"
    sections = extract_title_sections(text)
    assert "schedule_b2" in sections


def test_handles_requirements_variant():
    """'REQUIREMENTS TO TITLE' standalone header must be recognised as schedule_b1."""
    text = "SCHEDULE A\nPreamble\n\nREQUIREMENTS TO TITLE\nPay off mortgage\n"
    sections = extract_title_sections(text)
    assert "schedule_b1" in sections


def test_case_insensitive_detection():
    """Markers must be detected regardless of case."""
    text = "schedule a\nContent A\n\nschedule b-ii\nContent B2\n"
    sections = extract_title_sections(text)
    assert "schedule_a" in sections
    assert "schedule_b2" in sections


def test_section_text_does_not_bleed_into_next():
    """Each section's text must stop at the next section marker."""
    text = (
        "SCHEDULE A\n"
        "ONLY_IN_A\n\n"
        "SCHEDULE B-I\n"
        "ONLY_IN_B1\n\n"
        "SCHEDULE B-II\n"
        "ONLY_IN_B2\n"
    )
    sections = extract_title_sections(text)

    assert "ONLY_IN_A" in sections["schedule_a"]
    assert "ONLY_IN_B1" not in sections["schedule_a"]

    assert "ONLY_IN_B1" in sections["schedule_b1"]
    assert "ONLY_IN_B2" not in sections["schedule_b1"]

    assert "ONLY_IN_B2" in sections["schedule_b2"]


def test_partial_sections_supported():
    """A doc with only Schedule A and B-II (no B-I) must still work."""
    text = "SCHEDULE A\nContent A\n\nSCHEDULE B-II\nContent B2\n"
    sections = extract_title_sections(text)
    assert set(sections.keys()) == {"schedule_a", "schedule_b2"}


# ── build_title_prompt_text ────────────────────────────────────────────────────

def test_build_prompt_text_orders_sections():
    """Output must have A before B-I before B-II regardless of dict order."""
    sections = {
        "schedule_b2": "B2 content",
        "schedule_a": "A content",
        "schedule_b1": "B1 content",
    }
    result = build_title_prompt_text(sections)

    pos_a  = result.index("A content")
    pos_b1 = result.index("B1 content")
    pos_b2 = result.index("B2 content")
    assert pos_a < pos_b1 < pos_b2


def test_build_prompt_text_includes_labels():
    sections = {"schedule_a": "some text", "schedule_b2": "exceptions"}
    result = build_title_prompt_text(sections)
    assert "SCHEDULE A" in result
    assert "SCHEDULE B-II" in result
    # B-I (Requirements) label must not appear when that section is absent.
    # Use the full label to avoid false match from "SCHEDULE B-II" containing "SCHEDULE B-I".
    assert "SCHEDULE B-I (Requirements)" not in result


def test_build_prompt_text_returns_empty_string_on_empty_dict():
    assert build_title_prompt_text({}) == ""
