"""Closing Disclosure / HUD-1 rules — CD-001 through CD-006.

Day 5: added CD-003 seller credits cross-doc comparison and
CD-006 closing cost ratio check.
"""
from app.rules.base import BaseRule, RuleResult, Severity
from app.rules._helpers import parse_amount


class CD001(BaseRule):
    rule_id = "CD-001"
    category = "closing_disclosure"
    description = "Closing Disclosure or HUD-1 present"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        if not d.get("closing_disclosure") and not d.get("hud1"):
            return self._fail("Closing Disclosure or HUD-1 not found in package")
        return self._pass()


class CD002(BaseRule):
    rule_id = "CD-002"
    category = "closing_disclosure"
    description = "Cash to close amount documented"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        cd = d.get("closing_disclosure") or d.get("hud1")
        if not cd:
            return self._skipped()
        raw = cd.get("cash_to_close")
        if not raw:
            return self._fail("Cash to close amount not found")
        amount = parse_amount(raw)
        if amount is not None and amount <= 0:
            return self._fail(f"Cash to close is ${amount:,.2f} — must be positive")
        return self._pass(detail=f"Cash to close: {raw}")


class CD003(BaseRule):
    rule_id = "CD-003"
    category = "closing_disclosure"
    description = "Seller credits match purchase agreement"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        cd = d.get("closing_disclosure") or d.get("hud1")
        if not cd:
            return self._skipped()

        cd_credits_raw = cd.get("seller_credits")
        if not cd_credits_raw:
            return self._warning("Seller credits not found — verify against purchase agreement")

        pa = d.get("purchase_agreement", {})
        pa_credits_raw = pa.get("seller_credits") if pa else None
        if pa_credits_raw:
            cd_val = parse_amount(cd_credits_raw)
            pa_val = parse_amount(pa_credits_raw)
            if cd_val is not None and pa_val is not None:
                diff = abs(cd_val - pa_val)
                if diff > 100:
                    return self._warning(
                        f"Seller credits differ by ${diff:,.2f}: "
                        f"${pa_val:,.2f} (PA) vs ${cd_val:,.2f} (CD)",
                        refs=["purchase_agreement", "closing_disclosure"],
                    )

        return self._pass()


class CD004(BaseRule):
    rule_id = "CD-004"
    category = "closing_disclosure"
    description = "Prorated taxes calculated and documented"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        cd = d.get("closing_disclosure") or d.get("hud1")
        if not cd:
            return self._skipped()
        if not cd.get("prorated_taxes"):
            return self._warning("Prorated tax calculation not found")
        return self._pass()


class CD005(BaseRule):
    rule_id = "CD-005"
    category = "closing_disclosure"
    description = "Lender fees and origination charges itemized"
    severity = Severity.INFO

    async def check(self, d: dict) -> RuleResult:
        cd = d.get("closing_disclosure") or d.get("hud1")
        if not cd:
            return self._skipped()
        raw = cd.get("lender_fees") or cd.get("total_closing_costs")
        if not raw:
            return self._pass(detail="Lender fee itemization not extracted — review manually")
        return self._pass(detail=f"Closing costs: {raw}")


class CD006(BaseRule):
    rule_id = "CD-006"
    category = "closing_disclosure"
    description = "Total closing costs reasonable (< 5% of purchase price)"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        cd = d.get("closing_disclosure") or d.get("hud1")
        if not cd:
            return self._skipped()

        costs_raw = cd.get("total_closing_costs")
        pa = d.get("purchase_agreement", {})
        price_raw = pa.get("purchase_price") if pa else None

        if not costs_raw or not price_raw:
            return self._skipped("Requires total closing costs and purchase price")

        costs = parse_amount(costs_raw)
        price = parse_amount(price_raw)

        if costs is None or price is None or price == 0:
            return self._skipped("Could not parse closing costs or purchase price")

        ratio = costs / price
        if ratio > 0.05:
            return self._warning(
                f"Total closing costs are {ratio:.1%} of purchase price "
                f"(${costs:,.2f} of ${price:,.2f}) — exceeds 5% guideline",
                refs=["closing_disclosure", "purchase_agreement"],
            )
        return self._pass(detail=f"Closing cost ratio: {ratio:.1%}")


RULES = [CD001(), CD002(), CD003(), CD004(), CD005(), CD006()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
