"""
Day 6: Report builder.
Aggregates rule results into the final JSON report structure, enriched with:
- executive_brief (5 bullets via Claude)
- conflicts array (cross-doc FAIL/WARNING cards)
- action_plan (prioritized list via Claude)
"""
import json
import logging
from typing import Optional

from app.rules.base import RuleResult, RuleStatus, Severity

logger = logging.getLogger(__name__)
from app.llm.client import ClaudeResponseError, claude_json
from app.llm.prompts import EXECUTIVE_BRIEF_PROMPT, ACTION_PLAN_PROMPT

# Rules that represent cross-document comparisons — used to build conflict cards.
# Maps rule_id → (field_label, doc_type_a, field_key_a, doc_type_b, field_key_b)
_CROSS_DOC_FIELDS: dict[str, tuple] = {
    "PA-001": ("buyer/borrower name",      "purchase_agreement", "buyer_name",      "loan_note",          "borrower_name"),
    "PA-002": ("property address",          "purchase_agreement", "property_address", "mortgage_deed",      "property_address"),
    "PA-003": ("purchase price",            "purchase_agreement", "purchase_price",   "closing_disclosure", "purchase_price"),
    "LN-002": ("borrower/buyer name",       "loan_note",          "borrower_name",    "purchase_agreement", "buyer_name"),
    "TC-002": ("property address",          "purchase_agreement", "property_address", "title_commitment",   "legal_description"),
    "TC-007": ("title insurance vs price",  "title_commitment",   "insurance_amount", "purchase_agreement", "purchase_price"),
    "CC-001": ("buyer/borrower name",       "purchase_agreement", "buyer_name",       "loan_note",          "borrower_name"),
    "CC-002": ("property address",          "purchase_agreement", "property_address", "mortgage_deed",      "property_address"),
    "LN-001": ("loan vs purchase price",    "loan_note",          "loan_amount",      "purchase_agreement", "purchase_price"),
    "IN-002": ("coverage vs loan amount",   "insurance_binder",   "coverage_amount",  "loan_note",          "loan_amount"),
    "IN-005": ("insurance vs closing date", "insurance_binder",   "effective_date",   "purchase_agreement", "closing_date"),
    "CD-003": ("seller credits",            "purchase_agreement", "seller_credits",   "closing_disclosure", "seller_credits"),
    "CD-006": ("closing cost ratio",        "closing_disclosure", "total_closing_costs", "purchase_agreement", "purchase_price"),
}


def build_report(
    rule_results: list[RuleResult],
    fields_by_doc: Optional[dict] = None,
    classifications: Optional[dict] = None,
) -> dict:
    """
    Aggregate rule results into the full report payload.
    Optionally enriches with executive_brief and action_plan via Claude
    when `fields_by_doc` is provided.
    """
    passed  = [r for r in rule_results if r.status == RuleStatus.PASS]
    warnings = [r for r in rule_results if r.status == RuleStatus.WARNING]
    failed  = [r for r in rule_results if r.status == RuleStatus.FAIL]

    if failed:
        overall = "FAIL"
    elif warnings:
        overall = "WARNING"
    else:
        overall = "PASS"

    # Build conflicts array from FAIL / WARNING rules
    conflicts = _build_conflicts(rule_results, fields_by_doc or {})

    # Documents list from classifications
    documents = _build_documents(classifications or {}, rule_results)

    # Executive brief + action plan via Claude — both in parallel
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        brief_future = pool.submit(_get_executive_brief, rule_results)
        plan_future  = pool.submit(_get_action_plan, conflicts, failed, warnings)
        try:
            executive_brief = brief_future.result()
        except Exception as exc:
            logger.error("❌ Executive brief generation failed: %s", exc, exc_info=True)
            raise
        try:
            action_plan = plan_future.result()
        except Exception as exc:
            logger.error("❌ Action plan generation failed: %s", exc, exc_info=True)
            raise

    return {
        "overall": overall,
        "summary": {
            "total_rules": len(rule_results),
            "passed": len(passed),
            "warnings": len(warnings),
            "failed": len(failed),
        },
        "documents": documents,
        "results": [r.to_dict() for r in rule_results],
        "conflicts": conflicts,
        "executive_brief": executive_brief,
        "action_plan": action_plan,
    }


# ── conflicts ──────────────────────────────────────────────────────────────────

def _build_conflicts(rule_results: list[RuleResult], fields_by_doc: dict) -> list[dict]:
    conflicts = []
    for r in rule_results:
        if r.status not in (RuleStatus.FAIL, RuleStatus.WARNING):
            continue

        conflict = {
            "rule_id": r.rule_id,
            "type": r.description,
            "severity": r.severity.value,
            "message": r.detail or r.description,
            "resolved": False,
            "field": None,
            "doc_a": None,
            "value_a": None,
            "doc_b": None,
            "value_b": None,
        }

        # Enrich with doc_a / doc_b values if this is a known cross-doc rule
        meta = _CROSS_DOC_FIELDS.get(r.rule_id)
        if meta:
            field_label, dt_a, fk_a, dt_b, fk_b = meta
            conflict["field"] = field_label
            doc_a_fields = fields_by_doc.get(dt_a, {})
            doc_b_fields = fields_by_doc.get(dt_b, {})
            conflict["doc_a"] = dt_a.replace("_", " ").title()
            conflict["value_a"] = str(doc_a_fields.get(fk_a, "")) or None
            conflict["doc_b"] = dt_b.replace("_", " ").title()
            conflict["value_b"] = str(doc_b_fields.get(fk_b, "")) or None

        conflicts.append(conflict)

    return conflicts


# ── documents list ─────────────────────────────────────────────────────────────

def _build_documents(classifications: dict, rule_results: list[RuleResult]) -> list[dict]:
    # Determine which doc types have failures
    failing_doc_types: set[str] = set()
    warning_doc_types: set[str] = set()
    for r in rule_results:
        category_key = r.category
        if r.status == RuleStatus.FAIL:
            failing_doc_types.add(category_key)
        elif r.status == RuleStatus.WARNING:
            warning_doc_types.add(category_key)

    docs = []
    for filename, info in classifications.items():
        doc_type = info.get("document_type", "other")
        confidence = info.get("confidence", 0.0)

        if doc_type in failing_doc_types:
            status = "fail"
        elif doc_type in warning_doc_types or confidence < 0.7:
            status = "warn"
        else:
            status = "ok"

        docs.append({
            "filename": filename,
            "document_type": doc_type,
            "confidence": confidence,
            "status": status,
        })

    return docs


# ── Claude enrichment ──────────────────────────────────────────────────────────

def _get_executive_brief(rule_results: list[RuleResult]) -> list[str]:
    # Only include FAIL and WARNING results to keep the prompt focused
    notable = [r.to_dict() for r in rule_results
               if r.status in (RuleStatus.FAIL, RuleStatus.WARNING)][:20]
    if not notable:
        return ["All validation checks passed — file appears ready to close."]

    result = claude_json(
        EXECUTIVE_BRIEF_PROMPT.format(
            rule_results_json=json.dumps(notable, indent=2)
        ),
        max_tokens=1024,
    )
    bullets = result.get("bullets")
    if not isinstance(bullets, list) or len(bullets) == 0:
        raise ClaudeResponseError(
            f"Claude executive brief response is missing 'bullets' list. "
            f"Got: {result!r}. Check the EXECUTIVE_BRIEF_PROMPT template."
        )
    return bullets


def _get_action_plan(
    conflicts: list[dict],
    failed: list[RuleResult],
    warnings: list[RuleResult],
) -> list[dict]:
    notable_issues = [
        {"rule_id": r.rule_id, "description": r.description,
         "detail": r.detail, "severity": r.severity.value}
        for r in (failed + warnings)[:15]
    ]
    if not notable_issues:
        return []

    result = claude_json(
        ACTION_PLAN_PROMPT.format(
            conflicts_json=json.dumps(notable_issues, indent=2)
        ),
        max_tokens=1024,
    )
    if isinstance(result, list):
        return result
    for key in ("action_plan", "actions", "items"):
        if key in result and isinstance(result[key], list):
            return result[key]
    raise ClaudeResponseError(
        f"Claude action plan response is not a list and contains no recognizable key "
        f"('action_plan', 'actions', 'items'). Got: {result!r}. "
        f"Check the ACTION_PLAN_PROMPT template."
    )
