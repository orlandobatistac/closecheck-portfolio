"""Insurance rules — IN-001 through IN-005.

Day 5: added IN-002 numeric coverage vs loan comparison, IN-004 actual
flood zone check, IN-005 effective date vs closing date comparison.
"""
from app.rules.base import BaseRule, RuleResult, Severity
from app.rules._helpers import parse_amount, parse_date


class IN001(BaseRule):
    rule_id = "IN-001"
    category = "insurance"
    description = "Homeowner's insurance binder present"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        if not d.get("insurance_binder"):
            return self._fail("Homeowner's insurance binder not found in package")
        return self._pass()


class IN002(BaseRule):
    rule_id = "IN-002"
    category = "insurance"
    description = "Coverage amount meets or exceeds loan amount"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ins = d.get("insurance_binder", {})
        if not ins:
            return self._skipped()

        cov_raw = ins.get("coverage_amount")
        if not cov_raw:
            return self._fail("Coverage amount not found in insurance binder")

        coverage = parse_amount(cov_raw)
        if coverage is None:
            return self._warning(f"Coverage amount '{cov_raw}' could not be parsed")

        ln = d.get("loan_note", {})
        loan_raw = ln.get("loan_amount") if ln else None
        if loan_raw:
            loan = parse_amount(loan_raw)
            if loan is not None and coverage < loan:
                return self._fail(
                    f"Coverage amount (${coverage:,.2f}) is less than "
                    f"loan amount (${loan:,.2f})",
                    refs=["insurance_binder", "loan_note"],
                )

        return self._pass(detail=f"Coverage: ${coverage:,.2f}")


class IN003(BaseRule):
    rule_id = "IN-003"
    category = "insurance"
    description = "Lender listed as mortgagee"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ins = d.get("insurance_binder", {})
        if not ins:
            return self._skipped()
        if not ins.get("mortgagee"):
            return self._fail("Lender not listed as mortgagee on insurance binder")
        return self._pass(detail=f"Mortgagee: {ins['mortgagee']}")


class IN004(BaseRule):
    rule_id = "IN-004"
    category = "insurance"
    description = "Flood insurance present (if flood zone)"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ins = d.get("insurance_binder", {})
        if not ins:
            return self._skipped()

        flood_zone = ins.get("flood_zone")
        if flood_zone and str(flood_zone).upper() not in ("X", "X500", "NONE", "N/A", ""):
            # Non-X zones require flood insurance
            return self._fail(
                f"Property is in flood zone '{flood_zone}' — flood insurance required",
                refs=["insurance_binder"],
            )
        return self._pass(detail="No flood zone concern detected")


class IN005(BaseRule):
    rule_id = "IN-005"
    category = "insurance"
    description = "Policy effective on or before closing date"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ins = d.get("insurance_binder", {})
        if not ins:
            return self._skipped()

        eff_raw = ins.get("effective_date")
        if not eff_raw:
            return self._fail("Insurance effective date not found")

        eff = parse_date(eff_raw)
        if eff is None:
            return self._warning(f"Insurance effective date '{eff_raw}' could not be parsed")

        pa = d.get("purchase_agreement", {})
        closing_raw = pa.get("closing_date") if pa else None
        if closing_raw:
            closing = parse_date(closing_raw)
            if closing and eff > closing:
                return self._fail(
                    f"Insurance effective date ({eff}) is after closing date ({closing})",
                    refs=["insurance_binder", "purchase_agreement"],
                )

        return self._pass(detail=f"Effective: {eff_raw}")


RULES = [IN001(), IN002(), IN003(), IN004(), IN005()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
