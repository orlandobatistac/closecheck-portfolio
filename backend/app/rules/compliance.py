"""Identity & Compliance rules — IC-001 through IC-004.

Day 5: added IC-002 FIRPTA keyword detection, IC-003 wire routing/account
null check, IC-004 Power of Attorney keyword detection.
"""
import re

from app.rules.base import BaseRule, RuleResult, Severity

_FIRPTA_KEYWORDS = re.compile(
    r"\b(foreign|non.?resident alien|firpta|foreign national|nra)\b", re.IGNORECASE
)
_POA_KEYWORDS = re.compile(
    r"\b(power of attorney|poa|attorney.in.fact)\b", re.IGNORECASE
)


def _flatten(d: dict) -> str:
    return " ".join(str(v) for v in d.values() if v)


class IC001(BaseRule):
    rule_id = "IC-001"
    category = "compliance"
    description = "Government-issued ID for all parties documented"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        if not d.get("id_document"):
            return self._fail("Government-issued ID not found in package")
        return self._pass()


class IC002(BaseRule):
    rule_id = "IC-002"
    category = "compliance"
    description = "FIRPTA certificate present (if applicable)"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        pa = d.get("purchase_agreement", {})
        if pa and _FIRPTA_KEYWORDS.search(_flatten(pa)):
            return self._warning(
                "Foreign seller indicator detected in purchase agreement — "
                "FIRPTA certificate required"
            )
        return self._pass(detail="No FIRPTA indicator detected")


class IC003(BaseRule):
    rule_id = "IC-003"
    category = "compliance"
    description = "Wire instructions verified — no changes post-transmission"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        wire = d.get("wire_instructions", {})
        if not wire:
            return self._warning(
                "Wire instructions not found — verify wiring details before close"
            )

        missing = []
        if not wire.get("routing_number"):
            missing.append("routing number")
        if not wire.get("account_number"):
            missing.append("account number")
        if missing:
            return self._fail(
                f"Wire instructions incomplete — missing: {', '.join(missing)}"
            )

        return self._pass(detail="Wire instructions present with routing and account")


class IC004(BaseRule):
    rule_id = "IC-004"
    category = "compliance"
    description = "Power of Attorney documented and notarized (if applicable)"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        pa = d.get("purchase_agreement", {})
        if pa and _POA_KEYWORDS.search(_flatten(pa)):
            return self._warning(
                "Power of Attorney referenced in purchase agreement — "
                "ensure POA is notarized and on file"
            )
        return self._pass(detail="No POA reference detected — skip if all parties signing in person")


RULES = [IC001(), IC002(), IC003(), IC004()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
