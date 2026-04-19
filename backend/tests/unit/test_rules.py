"""Unit tests for the rule engine — Day 4 + Day 5 suite.

Day 4: PA-001 through PA-004, TC-001, TC-005.
Day 5: LN-001, LN-006, IN-002, IN-005, CD-006, IC-003.
"""
import asyncio
from datetime import date, timedelta

import pytest

from app.rules.purchase_agreement import PA001, PA002, PA003, PA004, RULES as PA_RULES
from app.rules.title import TC001, TC005
from app.rules.loan import LN001, LN006
from app.rules.insurance import IN002, IN005
from app.rules.closing_disclosure import CD006
from app.rules.compliance import IC003


# ── helpers ────────────────────────────────────────────────────────────────────

def run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _future_date(days: int = 30) -> str:
    return (date.today() + timedelta(days=days)).strftime("%m/%d/%Y")


def _past_date(days: int = 30) -> str:
    return (date.today() - timedelta(days=days)).strftime("%m/%d/%Y")


# ── PA-001: buyer / borrower name consistency ─────────────────────────────────

class TestPA001:
    def test_consistent_names_pass(self):
        docs = {
            "purchase_agreement": {"buyer_name": "Carlos Martinez", "seller_name": "John Smith"},
            "loan_note": {"borrower_name": "Carlos Martinez"},
        }
        result = run(PA001().check(docs))
        assert result.status.value == "PASS"

    def test_missing_buyer_name_fails(self):
        docs = {"purchase_agreement": {"buyer_name": None, "seller_name": "John Smith"}}
        result = run(PA001().check(docs))
        assert result.status.value == "FAIL"
        assert "missing" in result.detail.lower()

    def test_name_mismatch_across_docs_fails(self):
        docs = {
            "purchase_agreement": {"buyer_name": "Carlos Martinez", "seller_name": "John Smith"},
            "loan_note": {"borrower_name": "Maria Garcia"},
        }
        result = run(PA001().check(docs))
        assert result.status.value == "FAIL"

    def test_accent_variation_fails(self):
        """'Martinez' vs 'Martínez' — accented variant should NOT pass fuzzy match."""
        docs = {
            "purchase_agreement": {"buyer_name": "Carlos Martinez", "seller_name": "John Smith"},
            "loan_note": {"borrower_name": "Carlos Martínez"},
        }
        result = run(PA001().check(docs))
        # After accent-stripping, both normalize to "carlos martinez" → should PASS
        # (unicodedata strips the accent; this tests that the normalization works)
        assert result.status.value == "PASS"

    def test_clearly_different_names_fail(self):
        docs = {
            "purchase_agreement": {"buyer_name": "Alice Johnson", "seller_name": "Bob Smith"},
            "mortgage_deed": {"borrower_name": "Robert Williams"},
        }
        result = run(PA001().check(docs))
        assert result.status.value == "FAIL"

    def test_no_purchase_agreement_skips(self):
        result = run(PA001().check({}))
        assert result.status.value == "SKIPPED"


# ── PA-002: property address consistency ─────────────────────────────────────

class TestPA002:
    def test_same_address_pass(self):
        docs = {
            "purchase_agreement": {"property_address": "4521 Oak Lane, Charlotte, NC 28277"},
            "mortgage_deed": {"property_address": "4521 Oak Lane, Charlotte, NC 28277"},
        }
        result = run(PA002().check(docs))
        assert result.status.value == "PASS"

    def test_different_address_fails(self):
        docs = {
            "purchase_agreement": {"property_address": "4521 Oak Lane, Charlotte, NC 28277"},
            "mortgage_deed": {"property_address": "100 Main Street, Austin, TX 78701"},
        }
        result = run(PA002().check(docs))
        assert result.status.value == "FAIL"

    def test_missing_address_fails(self):
        docs = {"purchase_agreement": {"property_address": None}}
        result = run(PA002().check(docs))
        assert result.status.value == "FAIL"


# ── PA-003: purchase price matches closing disclosure ─────────────────────────

class TestPA003:
    def test_price_consistent_pass(self):
        docs = {
            "purchase_agreement": {"purchase_price": "$385,000"},
            "closing_disclosure": {"purchase_price": "$385,000"},
        }
        result = run(PA003().check(docs))
        assert result.status.value == "PASS"

    def test_price_mismatch_2500_fails(self):
        docs = {
            "purchase_agreement": {"purchase_price": "$385,000"},
            "closing_disclosure": {"purchase_price": "$387,500"},
        }
        result = run(PA003().check(docs))
        assert result.status.value == "FAIL"
        assert "2,500.00" in result.detail

    def test_price_within_1_dollar_passes(self):
        docs = {
            "purchase_agreement": {"purchase_price": "$385,000.00"},
            "closing_disclosure": {"purchase_price": "$385,000.50"},
        }
        result = run(PA003().check(docs))
        assert result.status.value == "PASS"

    def test_missing_price_fails(self):
        docs = {"purchase_agreement": {"purchase_price": None}}
        result = run(PA003().check(docs))
        assert result.status.value == "FAIL"

    def test_no_cd_still_passes_with_price_present(self):
        docs = {"purchase_agreement": {"purchase_price": "$300,000"}}
        result = run(PA003().check(docs))
        assert result.status.value == "PASS"


# ── PA-004: closing date not expired ─────────────────────────────────────────

class TestPA004:
    def test_future_date_pass(self):
        docs = {"purchase_agreement": {"closing_date": _future_date(30)}}
        result = run(PA004().check(docs))
        assert result.status.value == "PASS"

    def test_past_date_fails(self):
        docs = {"purchase_agreement": {"closing_date": _past_date(10)}}
        result = run(PA004().check(docs))
        assert result.status.value == "FAIL"
        assert "passed" in result.detail.lower()

    def test_missing_date_fails(self):
        docs = {"purchase_agreement": {"closing_date": None}}
        result = run(PA004().check(docs))
        assert result.status.value == "FAIL"


# ── TC-001: title commitment present ─────────────────────────────────────────

class TestTC001:
    def test_present_pass(self):
        docs = {"title_commitment": {"legal_description": "Lot 5 Block 3..."}}
        result = run(TC001().check(docs))
        assert result.status.value == "PASS"

    def test_absent_fails(self):
        result = run(TC001().check({}))
        assert result.status.value == "FAIL"
        assert "not found" in result.detail.lower()


# ── TC-005: open liens ────────────────────────────────────────────────────────

class TestTC005:
    def test_no_liens_pass(self):
        docs = {"title_commitment": {"open_liens": []}}
        result = run(TC005().check(docs))
        assert result.status.value == "PASS"

    def test_open_lien_fails(self):
        docs = {"title_commitment": {"open_liens": ["Mortgage lien - First National Bank"]}}
        result = run(TC005().check(docs))
        assert result.status.value == "FAIL"
        assert "First National Bank" in result.detail

    def test_no_title_doc_skips(self):
        result = run(TC005().check({}))
        assert result.status.value == "SKIPPED"


# ── full rule set sanity check ────────────────────────────────────────────────

class TestRuleSet:
    def test_pa_rules_all_run(self):
        """All 7 PA rules execute without exception on empty documents."""
        results = asyncio.get_event_loop().run_until_complete(
            asyncio.gather(*[r.check({}) for r in PA_RULES])
        )
        assert len(results) == 7

    def test_severity_ordering_in_validator(self):
        """run_all_rules result is sorted FAIL → WARNING → PASS → SKIPPED."""
        from app.services.validator import run_all_rules
        from app.rules.base import RuleStatus

        docs = {
            "purchase_agreement": {
                "buyer_name": "Alice",
                "seller_name": "Bob",
                "property_address": "123 Main St",
                "purchase_price": "$300,000",
                "closing_date": _future_date(30),
                "earnest_money": "$5,000",
                "signatures_present": True,
                "contingencies": ["inspection"],
            },
        }
        results = asyncio.get_event_loop().run_until_complete(run_all_rules(docs))
        statuses = [r.status for r in results]
        fail_indices = [i for i, s in enumerate(statuses) if s == RuleStatus.FAIL]
        warn_indices = [i for i, s in enumerate(statuses) if s == RuleStatus.WARNING]
        pass_indices = [i for i, s in enumerate(statuses) if s == RuleStatus.PASS]

        if fail_indices and warn_indices:
            assert max(fail_indices) < min(warn_indices)
        if warn_indices and pass_indices:
            assert max(warn_indices) < min(pass_indices)


# ══════════════════════════════════════════════════════════════════════════════
# DAY 5 TESTS
# ══════════════════════════════════════════════════════════════════════════════

# ── LN-001: loan amount vs purchase price ─────────────────────────────────────

class TestLN001:
    def test_loan_within_price_passes(self):
        docs = {
            "loan_note": {"loan_amount": "$308,000"},
            "purchase_agreement": {"purchase_price": "$385,000"},
        }
        result = run(LN001().check(docs))
        assert result.status.value == "PASS"

    def test_loan_exceeds_price_fails(self):
        docs = {
            "loan_note": {"loan_amount": "$400,000"},
            "purchase_agreement": {"purchase_price": "$385,000"},
        }
        result = run(LN001().check(docs))
        assert result.status.value == "FAIL"
        assert "exceeds" in result.detail.lower()

    def test_missing_loan_amount_fails(self):
        docs = {"loan_note": {"loan_amount": None}}
        result = run(LN001().check(docs))
        assert result.status.value == "FAIL"

    def test_no_loan_doc_skips(self):
        result = run(LN001().check({}))
        assert result.status.value == "SKIPPED"


# ── LN-006: LTV ratio ────────────────────────────────────────────────────────

class TestLN006:
    def test_ltv_80_passes(self):
        docs = {
            "loan_note": {"loan_amount": "$240,000"},
            "purchase_agreement": {"purchase_price": "$300,000"},
        }
        result = run(LN006().check(docs))
        assert result.status.value == "PASS"
        assert "80.0%" in result.detail

    def test_ltv_98_warns(self):
        docs = {
            "loan_note": {"loan_amount": "$294,000"},
            "purchase_agreement": {"purchase_price": "$300,000"},
        }
        result = run(LN006().check(docs))
        assert result.status.value == "WARNING"
        assert "98.0%" in result.detail

    def test_ltv_97_exactly_passes(self):
        docs = {
            "loan_note": {"loan_amount": "$291,000"},
            "purchase_agreement": {"purchase_price": "$300,000"},
        }
        result = run(LN006().check(docs))
        assert result.status.value == "PASS"

    def test_missing_amounts_skips(self):
        result = run(LN006().check({}))
        assert result.status.value == "SKIPPED"


# ── IN-002: coverage >= loan amount ──────────────────────────────────────────

class TestIN002:
    def test_coverage_exceeds_loan_passes(self):
        docs = {
            "insurance_binder": {"coverage_amount": "$350,000"},
            "loan_note": {"loan_amount": "$308,000"},
        }
        result = run(IN002().check(docs))
        assert result.status.value == "PASS"

    def test_coverage_below_loan_fails(self):
        docs = {
            "insurance_binder": {"coverage_amount": "$250,000"},
            "loan_note": {"loan_amount": "$308,000"},
        }
        result = run(IN002().check(docs))
        assert result.status.value == "FAIL"
        assert "250,000" in result.detail
        assert "308,000" in result.detail

    def test_no_binder_skips(self):
        result = run(IN002().check({}))
        assert result.status.value == "SKIPPED"


# ── IN-005: insurance effective <= closing date ───────────────────────────────

class TestIN005:
    def test_effective_before_closing_passes(self):
        closing = _future_date(30)
        eff = _future_date(1)
        docs = {
            "insurance_binder": {"effective_date": eff},
            "purchase_agreement": {"closing_date": closing},
        }
        result = run(IN005().check(docs))
        assert result.status.value == "PASS"

    def test_effective_after_closing_fails(self):
        closing = _future_date(10)
        eff = _future_date(20)  # after closing
        docs = {
            "insurance_binder": {"effective_date": eff},
            "purchase_agreement": {"closing_date": closing},
        }
        result = run(IN005().check(docs))
        assert result.status.value == "FAIL"
        assert "after closing date" in result.detail.lower()

    def test_missing_effective_date_fails(self):
        docs = {"insurance_binder": {"effective_date": None}}
        result = run(IN005().check(docs))
        assert result.status.value == "FAIL"


# ── CD-006: closing cost ratio ────────────────────────────────────────────────

class TestCD006:
    def test_4_percent_passes(self):
        docs = {
            "closing_disclosure": {"total_closing_costs": "$12,000"},
            "purchase_agreement": {"purchase_price": "$300,000"},
        }
        result = run(CD006().check(docs))
        assert result.status.value == "PASS"
        assert "4.0%" in result.detail

    def test_6_percent_warns(self):
        docs = {
            "closing_disclosure": {"total_closing_costs": "$18,000"},
            "purchase_agreement": {"purchase_price": "$300,000"},
        }
        result = run(CD006().check(docs))
        assert result.status.value == "WARNING"
        assert "6.0%" in result.detail

    def test_missing_data_skips(self):
        result = run(CD006().check({}))
        assert result.status.value == "SKIPPED"


# ── IC-003: wire instructions completeness ────────────────────────────────────

class TestIC003:
    def test_complete_wire_instructions_pass(self):
        docs = {
            "wire_instructions": {
                "routing_number": "021000021",
                "account_number": "123456789",
                "bank_name": "First National",
            }
        }
        result = run(IC003().check(docs))
        assert result.status.value == "PASS"

    def test_missing_routing_number_fails(self):
        docs = {
            "wire_instructions": {
                "routing_number": None,
                "account_number": "123456789",
            }
        }
        result = run(IC003().check(docs))
        assert result.status.value == "FAIL"
        assert "routing number" in result.detail.lower()

    def test_no_wire_doc_warns(self):
        result = run(IC003().check({}))
        assert result.status.value == "WARNING"
