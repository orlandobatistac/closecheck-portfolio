"""Shared helpers for rule modules: amount parsing, date parsing, fuzzy matching."""
import difflib
import re
import unicodedata
from datetime import date, datetime


_DATE_FMTS = [
    "%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y",
    "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d",
]


def normalize_str(s: str) -> str:
    """Lowercase, strip accents and punctuation for comparison."""
    nfkd = unicodedata.normalize("NFKD", str(s))
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]", "", ascii_only.lower()).strip()


def fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return difflib.SequenceMatcher(None, normalize_str(a), normalize_str(b)).ratio() >= threshold


def parse_amount(s) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def parse_date(s) -> date | None:
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None
