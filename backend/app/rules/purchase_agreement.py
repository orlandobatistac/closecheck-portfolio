"""Purchase Agreement rules — PA-001 through PA-007.

Day 4: implemented fuzzy name matching (difflib), cross-document address and
price comparison, and closing-date expiry check.
"""
import difflib
import re
import unicodedata
from datetime import date, datetime

from app.rules.base import BaseRule, RuleResult, Severity

# ── helpers ────────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    """Lowercase, strip accents/punctuation for fuzzy comparison."""
    nfkd = unicodedata.normalize("NFKD", str(s))
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9 ]", "", ascii_only.lower()).strip()


def _fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio() >= threshold


def _parse_price(s) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


_DATE_FMTS = [
    "%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y",
    "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d",
]


def _parse_date(s) -> date | None:
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


# ── rules ─────────────────────────────────────────────────────────────────────

class PA001(BaseRule):
    rule_id = "PA-001"
    category = "purchase_agreement"
    description = "Buyer and seller names present and consistent across docs"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped("No purchase agreement found")

        buyer = pa.get("buyer_name")
        seller = pa.get("seller_name")
        if not buyer or not seller:
            return self._fail("Buyer or seller name missing in purchase agreement")

        # Cross-doc: compare buyer_name with borrower_name in loan / mortgage docs
        refs = ["purchase_agreement"]
        mismatches = []
        for doc_type in ("loan_note", "mortgage_deed"):
            other = documents.get(doc_type, {})
            borrower = other.get("borrower_name")
            if borrower and not _fuzzy_match(buyer, borrower):
                mismatches.append(
                    f"'{buyer}' (purchase_agreement) ≠ '{borrower}' ({doc_type})"
                )
                refs.append(doc_type)

        if mismatches:
            return self._fail("; ".join(mismatches), refs=refs)
        return self._pass(detail=f"Buyer: {buyer}", refs=refs)


class PA002(BaseRule):
    rule_id = "PA-002"
    category = "purchase_agreement"
    description = "Property address consistent across all documents"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()

        pa_addr = pa.get("property_address")
        if not pa_addr:
            return self._fail("Property address not found in purchase agreement")

        refs = ["purchase_agreement"]
        mismatches = []
        for doc_type in ("title_commitment", "mortgage_deed", "closing_disclosure"):
            other = documents.get(doc_type, {})
            addr = other.get("property_address")
            if addr and not _fuzzy_match(pa_addr, addr, threshold=0.80):
                mismatches.append(
                    f"'{pa_addr}' (purchase_agreement) ≠ '{addr}' ({doc_type})"
                )
                refs.append(doc_type)

        if mismatches:
            return self._fail("; ".join(mismatches), refs=refs)
        return self._pass(detail=f"Address: {pa_addr}", refs=refs)


class PA003(BaseRule):
    rule_id = "PA-003"
    category = "purchase_agreement"
    description = "Purchase price present and matches HUD/CD"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()

        pa_price_raw = pa.get("purchase_price")
        if not pa_price_raw:
            return self._fail("Purchase price not found in purchase agreement")

        pa_price = _parse_price(pa_price_raw)
        if pa_price is None:
            return self._warning(
                f"Purchase price '{pa_price_raw}' could not be parsed as a number"
            )

        refs = ["purchase_agreement"]
        for doc_type in ("closing_disclosure", "hud1"):
            other = documents.get(doc_type, {})
            other_raw = other.get("purchase_price") or other.get("cash_to_close")
            if other_raw:
                other_price = _parse_price(other_raw)
                if other_price is not None and abs(pa_price - other_price) > 1.00:
                    diff = abs(pa_price - other_price)
                    refs.append(doc_type)
                    return self._fail(
                        f"Purchase price mismatch of ${diff:,.2f}: "
                        f"${pa_price:,.2f} (purchase_agreement) vs "
                        f"${other_price:,.2f} ({doc_type})",
                        refs=refs,
                    )
                refs.append(doc_type)

        return self._pass(detail=f"Purchase price: ${pa_price:,.2f}", refs=refs)


class PA004(BaseRule):
    rule_id = "PA-004"
    category = "purchase_agreement"
    description = "Closing date present and not expired"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()

        raw = pa.get("closing_date")
        if not raw:
            return self._fail("Closing date not found in purchase agreement")

        closing = _parse_date(raw)
        if closing is None:
            return self._warning(
                f"Closing date '{raw}' could not be parsed — verify manually"
            )

        today = date.today()
        if closing < today:
            return self._fail(
                f"Closing date {closing.strftime('%b %d, %Y')} has already passed "
                f"(today is {today.strftime('%b %d, %Y')})"
            )

        return self._pass(detail=f"Closing date: {closing.strftime('%b %d, %Y')}")


class PA005(BaseRule):
    rule_id = "PA-005"
    category = "purchase_agreement"
    description = "Earnest money deposit amount documented"
    severity = Severity.WARNING

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()
        if not pa.get("earnest_money"):
            return self._warning("Earnest money deposit amount not found")
        return self._pass()


class PA006(BaseRule):
    rule_id = "PA-006"
    category = "purchase_agreement"
    description = "All required signatures present"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()
        sigs = pa.get("signatures_present")
        if sigs is None:
            return self._fail("Signature status not detected in purchase agreement")
        # Accept truthy values: True, "yes", "true", non-empty strings
        if isinstance(sigs, bool):
            if not sigs:
                return self._fail("Required signatures not present")
        elif str(sigs).lower() in ("false", "no", "missing", "unsigned", "0", ""):
            return self._fail(f"Required signatures not present: {sigs}")
        return self._pass()


class PA007(BaseRule):
    rule_id = "PA-007"
    category = "purchase_agreement"
    description = "Contingencies noted (inspection, financing, appraisal)"
    severity = Severity.INFO

    async def check(self, documents: dict) -> RuleResult:
        pa = documents.get("purchase_agreement", {})
        if not pa:
            return self._skipped()
        contingencies = pa.get("contingencies", [])
        if not contingencies:
            return self._warning("No contingencies documented — verify this is intentional")
        if isinstance(contingencies, list):
            return self._pass(detail=f"Contingencies: {', '.join(str(c) for c in contingencies)}")
        return self._pass(detail=f"Contingencies: {contingencies}")


RULES = [PA001(), PA002(), PA003(), PA004(), PA005(), PA006(), PA007()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
