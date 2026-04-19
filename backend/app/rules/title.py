"""Title Commitment rules — TC-001 through TC-007.

Day 4: added 6-month effective-date check (TC-003) and insurance-amount
comparison against purchase_price (TC-007).
"""
import re
from datetime import date, datetime, timedelta

from app.rules.base import BaseRule, RuleResult, Severity

# ── helpers ────────────────────────────────────────────────────────────────────

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


def _parse_amount(s) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


# ── rules ─────────────────────────────────────────────────────────────────────

class TC001(BaseRule):
    rule_id = "TC-001"
    category = "title"
    description = "Title commitment present"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        if not documents.get("title_commitment"):
            return self._fail("Title commitment not found in package")
        return self._pass()


class TC002(BaseRule):
    rule_id = "TC-002"
    category = "title"
    description = "Property legal description matches purchase agreement"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()
        if not tc.get("legal_description"):
            return self._fail("Legal description missing in title commitment")
        return self._pass()


class TC003(BaseRule):
    rule_id = "TC-003"
    category = "title"
    description = "Effective date within 6 months"
    severity = Severity.WARNING

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()

        raw = tc.get("effective_date")
        if not raw:
            return self._warning("Effective date not found — verify title commitment is current")

        eff = _parse_date(raw)
        if eff is None:
            return self._warning(f"Effective date '{raw}' could not be parsed — verify manually")

        cutoff = date.today() - timedelta(days=180)
        if eff < cutoff:
            age_days = (date.today() - eff).days
            return self._warning(
                f"Title commitment effective date ({eff.strftime('%b %d, %Y')}) "
                f"is {age_days} days old — exceeds 6-month guideline"
            )

        return self._pass(detail=f"Effective date: {eff.strftime('%b %d, %Y')}")


class TC004(BaseRule):
    rule_id = "TC-004"
    category = "title"
    description = "Schedule B exceptions reviewed and noted"
    severity = Severity.WARNING

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()
        exceptions = tc.get("schedule_b_exceptions", [])
        if exceptions:
            count = len(exceptions) if isinstance(exceptions, list) else 1
            return self._warning(
                f"{count} Schedule B exception(s) require review",
                refs=["title_commitment"],
            )
        return self._pass()


class TC005(BaseRule):
    rule_id = "TC-005"
    category = "title"
    description = "Open liens flagged"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()
        liens = tc.get("open_liens", [])
        if liens:
            if isinstance(liens, list):
                parts = []
                for lien in liens:
                    if isinstance(lien, dict):
                        parts.append(lien.get("description") or lien.get("requirement") or str(lien))
                    else:
                        parts.append(str(lien))
                label = "; ".join(parts)
            else:
                label = str(liens)
            return self._fail(f"Open liens detected: {label}")
        return self._pass()


class TC006(BaseRule):
    rule_id = "TC-006"
    category = "title"
    description = "Judgments or encumbrances identified"
    severity = Severity.FAIL

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()
        if tc.get("judgments"):
            return self._fail("Judgments or encumbrances found on title")
        return self._pass()


class TC007(BaseRule):
    rule_id = "TC-007"
    category = "title"
    description = "Title insurance amount matches purchase price"
    severity = Severity.WARNING

    async def check(self, documents: dict) -> RuleResult:
        tc = documents.get("title_commitment", {})
        if not tc:
            return self._skipped()

        ins_raw = tc.get("insurance_amount")
        if not ins_raw:
            return self._warning("Title insurance amount not found")

        # Claude may return {"owner_policy": "$485,000", "loan_policy": "$388,000"}
        if isinstance(ins_raw, dict):
            ins_raw = (ins_raw.get("owner_policy") or ins_raw.get("loan_policy")
                       or next(iter(ins_raw.values()), None))

        ins_amount = _parse_amount(ins_raw)
        if ins_amount is None:
            return self._warning(f"Title insurance amount '{ins_raw}' could not be parsed")

        # Compare against purchase_price from purchase_agreement if present
        pa = documents.get("purchase_agreement", {})
        pa_price_raw = pa.get("purchase_price")
        if pa_price_raw:
            pa_price = _parse_amount(pa_price_raw)
            if pa_price and ins_amount < pa_price * 0.99:
                return self._warning(
                    f"Title insurance amount (${ins_amount:,.2f}) is less than "
                    f"purchase price (${pa_price:,.2f})",
                    refs=["title_commitment", "purchase_agreement"],
                )

        return self._pass(detail=f"Insurance amount: ${ins_amount:,.2f}")


RULES = [TC001(), TC002(), TC003(), TC004(), TC005(), TC006(), TC007()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
