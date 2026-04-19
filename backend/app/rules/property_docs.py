"""Property document rules — PR-001 through PR-005.

Day 5: added keyword-based PR-003 HOA detection, PR-005 new construction
detection from purchase agreement text.
"""
import re

from app.rules.base import BaseRule, RuleResult, Severity
from app.rules._helpers import parse_amount

_NEW_CONSTRUCTION_KEYWORDS = re.compile(
    r"\b(new construction|builder|new home|newly built|new build)\b", re.IGNORECASE
)
_HOA_KEYWORDS = re.compile(
    r"\b(hoa|homeowners? association|home owner.?s association)\b", re.IGNORECASE
)


def _pa_text(pa: dict) -> str:
    """Flatten all PA field values into a single string for keyword search."""
    return " ".join(str(v) for v in pa.values() if v)


class PR001(BaseRule):
    rule_id = "PR-001"
    category = "property"
    description = "Property tax status — no delinquent taxes"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        tc = d.get("tax_certificate", {})
        if not tc:
            return self._skipped("Tax certificate not found")

        delinquent = tc.get("delinquent")
        if delinquent and str(delinquent).lower() not in ("false", "no", "none", "0", ""):
            amount = tc.get("delinquent_amount") or tc.get("amount_due")
            detail = f"Delinquent property taxes detected"
            if amount:
                detail += f": ${parse_amount(amount):,.2f}" if parse_amount(amount) else f": {amount}"
            return self._fail(detail)

        return self._pass()


class PR002(BaseRule):
    rule_id = "PR-002"
    category = "property"
    description = "Survey present (if required by lender)"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        if not d.get("survey"):
            return self._warning("Survey not found — verify lender requirements")
        return self._pass()


class PR003(BaseRule):
    rule_id = "PR-003"
    category = "property"
    description = "HOA documents present (if applicable)"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        if d.get("hoa_document"):
            return self._pass(detail="HOA document found")

        # Check if purchase agreement mentions HOA
        pa = d.get("purchase_agreement", {})
        if pa and _HOA_KEYWORDS.search(_pa_text(pa)):
            return self._warning(
                "Purchase agreement mentions HOA but no HOA document found in package"
            )

        return self._pass(detail="No HOA indication detected — skip if property is not in HOA")


class PR004(BaseRule):
    rule_id = "PR-004"
    category = "property"
    description = "HOA dues current — no outstanding balance"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        hoa = d.get("hoa_document", {})
        if not hoa:
            return self._skipped("No HOA document found")

        bal_raw = hoa.get("outstanding_balance")
        if bal_raw:
            bal = parse_amount(bal_raw)
            if bal is not None and bal > 0:
                return self._fail(f"Outstanding HOA balance: ${bal:,.2f}")
            elif bal is None and str(bal_raw).strip() not in ("0", "0.00", "none", ""):
                return self._fail(f"Outstanding HOA balance: {bal_raw}")

        return self._pass()


class PR005(BaseRule):
    rule_id = "PR-005"
    category = "property"
    description = "Certificate of Occupancy present (new construction)"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        pa = d.get("purchase_agreement", {})
        if pa and _NEW_CONSTRUCTION_KEYWORDS.search(_pa_text(pa)):
            if not d.get("certificate_of_occupancy"):
                return self._warning(
                    "New construction detected in purchase agreement — "
                    "Certificate of Occupancy not found"
                )

        return self._pass(detail="CO check: no new construction indicator found")


RULES = [PR001(), PR002(), PR003(), PR004(), PR005()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
