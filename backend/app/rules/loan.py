"""Loan / Mortgage rules — LN-001 through LN-006.

Day 5: added numeric LN-001 loan vs purchase_price check, LN-002 fuzzy
borrower/buyer match, and LN-006 LTV ratio calculation.
"""
from app.rules.base import BaseRule, RuleResult, Severity
from app.rules._helpers import fuzzy_match, parse_amount


class LN001(BaseRule):
    rule_id = "LN-001"
    category = "loan"
    description = "Loan amount consistent with purchase price and down payment"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ln = d.get("loan_note", {})
        if not ln:
            return self._skipped()

        loan_raw = ln.get("loan_amount")
        if not loan_raw:
            return self._fail("Loan amount not found in loan documents")

        loan = parse_amount(loan_raw)
        if loan is None:
            return self._warning(f"Loan amount '{loan_raw}' could not be parsed")

        pa = d.get("purchase_agreement", {})
        price_raw = pa.get("purchase_price")
        if price_raw:
            price = parse_amount(price_raw)
            if price and loan > price:
                return self._fail(
                    f"Loan amount (${loan:,.2f}) exceeds purchase price (${price:,.2f})",
                    refs=["loan_note", "purchase_agreement"],
                )

        return self._pass(detail=f"Loan amount: ${loan:,.2f}")


class LN002(BaseRule):
    rule_id = "LN-002"
    category = "loan"
    description = "Borrower name matches buyer name"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        ln = d.get("loan_note", {})
        if not ln:
            return self._skipped()

        borrower = ln.get("borrower_name")
        if not borrower:
            return self._fail("Borrower name not found in loan documents")

        pa = d.get("purchase_agreement", {})
        buyer = pa.get("buyer_name")
        if buyer and not fuzzy_match(borrower, buyer):
            return self._fail(
                f"Borrower name mismatch: '{borrower}' (loan) vs '{buyer}' (purchase agreement)",
                refs=["loan_note", "purchase_agreement"],
            )

        return self._pass(detail=f"Borrower: {borrower}")


class LN003(BaseRule):
    rule_id = "LN-003"
    category = "loan"
    description = "Interest rate and loan type documented"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        ln = d.get("loan_note", {})
        if not ln:
            return self._skipped()
        missing = []
        if not ln.get("interest_rate"):
            missing.append("interest rate")
        if not ln.get("loan_type"):
            missing.append("loan type")
        if missing:
            return self._warning(f"Missing from loan documents: {', '.join(missing)}")
        return self._pass(
            detail=f"Rate: {ln['interest_rate']}, Type: {ln['loan_type']}"
        )


class LN004(BaseRule):
    rule_id = "LN-004"
    category = "loan"
    description = "Promissory note present"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        if not d.get("loan_note"):
            return self._fail("Promissory note not found in package")
        return self._pass()


class LN005(BaseRule):
    rule_id = "LN-005"
    category = "loan"
    description = "Mortgage/Deed of Trust present"
    severity = Severity.FAIL

    async def check(self, d: dict) -> RuleResult:
        if not d.get("mortgage_deed"):
            return self._fail("Mortgage or Deed of Trust not found in package")
        return self._pass()


class LN006(BaseRule):
    rule_id = "LN-006"
    category = "loan"
    description = "Loan-to-value ratio within acceptable range"
    severity = Severity.WARNING

    async def check(self, d: dict) -> RuleResult:
        ln = d.get("loan_note", {})
        pa = d.get("purchase_agreement", {})

        loan = parse_amount(ln.get("loan_amount") if ln else None)
        price = parse_amount(pa.get("purchase_price") if pa else None)

        if loan is None or price is None or price == 0:
            return self._skipped("LTV requires loan amount and purchase price")

        ltv = loan / price
        if ltv > 0.97:
            return self._warning(
                f"LTV ratio {ltv:.1%} exceeds conventional maximum (97%)",
                refs=["loan_note", "purchase_agreement"],
            )
        return self._pass(detail=f"LTV: {ltv:.1%}")


RULES = [LN001(), LN002(), LN003(), LN004(), LN005(), LN006()]


async def run(documents: dict) -> list[RuleResult]:
    return [await rule.check(documents) for rule in RULES]
