"""
Day 6: Cross-document consistency checks.
Compares key fields extracted from multiple documents and flags mismatches via Claude.
"""
import json

from app.llm.client import claude_json
from app.llm.prompts import CONSISTENCY_CHECK_PROMPT
from app.rules.base import RuleResult, RuleStatus, Severity


def run_consistency_checks(documents: dict) -> list[RuleResult]:
    """
    Run cross-document field consistency checks.
    Returns one RuleResult per check (CC-001, CC-002).
    Only runs checks where at least two document sources have the relevant field.
    """
    return [
        r for r in [
            _check_name_consistency(documents),
            _check_address_consistency(documents),
        ]
        if r is not None
    ]


def _check_name_consistency(documents: dict) -> RuleResult:
    values: dict[str, str] = {}
    pa_buyer = documents.get("purchase_agreement", {}).get("buyer_name")
    ln_borrower = documents.get("loan_note", {}).get("borrower_name")
    md_borrower = documents.get("mortgage_deed", {}).get("borrower_name")
    if pa_buyer:
        values["purchase_agreement (buyer_name)"] = pa_buyer
    if ln_borrower:
        values["loan_note (borrower_name)"] = ln_borrower
    if md_borrower:
        values["mortgage_deed (borrower_name)"] = md_borrower

    if len(values) < 2:
        return RuleResult(
            rule_id="CC-001",
            category="consistency",
            description="Buyer / borrower name consistent across documents",
            severity=Severity.FAIL,
            status=RuleStatus.SKIPPED,
            detail="Not enough documents to compare names",
        )

    return _call_claude(
        rule_id="CC-001",
        description="Buyer / borrower name consistent across documents",
        values=values,
    )


def _check_address_consistency(documents: dict) -> RuleResult:
    values: dict[str, str] = {}
    pa_addr = documents.get("purchase_agreement", {}).get("property_address")
    md_addr = documents.get("mortgage_deed", {}).get("property_address")
    if pa_addr:
        values["purchase_agreement"] = pa_addr
    if md_addr:
        values["mortgage_deed"] = md_addr

    if len(values) < 2:
        return RuleResult(
            rule_id="CC-002",
            category="consistency",
            description="Property address consistent across documents",
            severity=Severity.FAIL,
            status=RuleStatus.SKIPPED,
            detail="Not enough documents to compare addresses",
        )

    return _call_claude(
        rule_id="CC-002",
        description="Property address consistent across documents",
        values=values,
    )


def _call_claude(rule_id: str, description: str, values: dict) -> RuleResult:
    comparison = {description: values}
    result = claude_json(
        CONSISTENCY_CHECK_PROMPT.format(
            comparison_json=json.dumps(comparison, indent=2)
        )
    )
    consistent = result.get("consistent", True)
    mismatches = result.get("mismatches", [])
    notes = result.get("notes", "")

    if consistent and not mismatches:
        return RuleResult(
            rule_id=rule_id,
            category="consistency",
            description=description,
            severity=Severity.FAIL,
            status=RuleStatus.PASS,
            detail=notes or "Values are consistent across documents",
            documents_referenced=list(values.keys()),
        )

    detail = "; ".join(
        m.get("explanation", "") for m in mismatches if m.get("explanation")
    ) or notes
    return RuleResult(
        rule_id=rule_id,
        category="consistency",
        description=description,
        severity=Severity.FAIL,
        status=RuleStatus.FAIL,
        detail=detail,
        documents_referenced=list(values.keys()),
    )
