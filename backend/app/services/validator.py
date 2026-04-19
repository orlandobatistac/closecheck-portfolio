"""
Rule engine: runs all registered rule modules against extracted document data.
"""
from app.rules.base import RuleResult, RuleStatus, Severity
from app.rules import (
    purchase_agreement,
    title,
    loan,
    closing_disclosure,
    property_docs,
    insurance,
    compliance,
)

ALL_RULE_MODULES = [
    purchase_agreement,
    title,
    loan,
    closing_disclosure,
    property_docs,
    insurance,
    compliance,
]

# Severity sort order: FAIL first, then WARNING, INFO, PASS, SKIPPED
_SEVERITY_ORDER = {
    RuleStatus.FAIL: 0,
    RuleStatus.WARNING: 1,
    RuleStatus.PASS: 2,
    RuleStatus.SKIPPED: 3,
}


async def run_rules(documents: dict, rule_modules: list | None = None) -> list[RuleResult]:
    """
    Run the given rule modules (or all if None) against extracted document data.
    Returns results sorted by severity: FAIL → WARNING → PASS → SKIPPED.
    `documents` is a dict keyed by document_type with extracted field dicts.
    """
    modules = rule_modules if rule_modules is not None else ALL_RULE_MODULES
    results: list[RuleResult] = []
    for module in modules:
        module_results = await module.run(documents)
        results.extend(module_results)

    results.sort(key=lambda r: _SEVERITY_ORDER.get(r.status, 4))
    return results


async def run_all_rules(documents: dict) -> list[RuleResult]:
    """Convenience wrapper: run every registered rule module."""
    return await run_rules(documents, ALL_RULE_MODULES)
