"""
Pipeline latency benchmark.
Measures each Claude call independently using a realistic but small payload.
Run from: backend/ directory
  py benchmark_pipeline.py
"""
import json
import os
import sys
import time
from statistics import mean, median

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_HERE, ".env"))

from app.llm.client import claude_json, claude_text
from app.llm.prompts import (
    CLASSIFIER_PROMPT,
    FIELD_EXTRACTOR_PROMPT,
    EXECUTIVE_BRIEF_PROMPT,
    ACTION_PLAN_PROMPT,
    CONSISTENCY_CHECK_PROMPT,
    FIELDS_BY_DOC_TYPE,
)

# ── Sample payloads ──────────────────────────────────────────────────────────

SAMPLE_TEXT = """
PURCHASE AND SALE AGREEMENT

Buyer: John A. Martinez
Seller: Sarah L. Thompson
Property Address: 4821 Clearwater Drive, Charlotte, NC 28210
Purchase Price: $485,000.00
Closing Date: May 15, 2026
Earnest Money Deposit: $9,700.00

The parties agree to the terms set forth herein. Buyer's financing contingency is 21 days.
Seller agrees to pay up to $5,000 in closing costs. Both parties have signed below.

/s/ John A. Martinez          /s/ Sarah L. Thompson
Date: 04/01/2026              Date: 04/01/2026
""" * 10  # Realistic size ~2500 chars

SAMPLE_RULE_RESULTS = [
    {"rule_id": "PA-001", "status": "FAIL", "severity": "FAIL",
     "description": "Buyer/borrower name consistent across documents",
     "detail": "Purchase Agreement has 'John A. Martinez' but Loan Note has 'John Martinez'"},
    {"rule_id": "PA-003", "status": "FAIL", "severity": "FAIL",
     "description": "Purchase price matches closing disclosure",
     "detail": "Purchase Agreement: $485,000 vs Closing Disclosure: $480,000"},
    {"rule_id": "TC-002", "status": "WARNING", "severity": "WARNING",
     "description": "Property address matches title commitment",
     "detail": "Minor discrepancy in street abbreviation (Drive vs Dr)"},
    {"rule_id": "IN-002", "status": "FAIL", "severity": "FAIL",
     "description": "Insurance coverage >= loan amount",
     "detail": "Coverage $400,000 is below loan amount $388,000 — check policy limits"},
    {"rule_id": "CD-006", "status": "WARNING", "severity": "WARNING",
     "description": "Closing costs within normal range",
     "detail": "Total closing costs $14,550 represent 3.0% of purchase price (typical 2-5%)"},
]

SAMPLE_CONFLICTS = [
    {"rule_id": "PA-001", "description": "Buyer/borrower name mismatch",
     "detail": "Purchase Agreement: 'John A. Martinez' vs Loan Note: 'John Martinez'",
     "severity": "FAIL"},
    {"rule_id": "PA-003", "description": "Purchase price mismatch",
     "detail": "Purchase Agreement: $485,000 vs Closing Disclosure: $480,000",
     "severity": "FAIL"},
    {"rule_id": "IN-002", "description": "Insurance coverage shortfall",
     "detail": "Coverage $400,000 is below loan amount $388,000",
     "severity": "FAIL"},
]

DOCUMENT_TYPES = [
    "purchase_agreement", "title_commitment", "closing_disclosure", "hud1",
    "loan_note", "mortgage_deed", "insurance_binder", "survey",
    "hoa_document", "tax_certificate", "id_document", "wire_instructions", "other",
]


# ── Benchmark helpers ────────────────────────────────────────────────────────

def time_call(label: str, fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    print(f"  {label:<40} {elapsed:>6.2f}s")
    return result, elapsed


def run_benchmark():
    print("\n" + "=" * 60)
    print("  CloseCheck Pipeline Latency Benchmark")
    print(f"  Model: claude-sonnet-4-6")
    print("=" * 60)

    timings = {}

    # ── Phase 1: Classification ──────────────────────────────────────
    print("\n[Phase 2] Classification (1 doc)")
    prompt = CLASSIFIER_PROMPT.format(
        document_types=", ".join(DOCUMENT_TYPES),
        text=SAMPLE_TEXT[:8000],
    )
    _, t = time_call("classify_document()", claude_json, prompt)
    timings["classify_1_doc"] = t

    # ── Phase 2: Field Extraction ────────────────────────────────────
    print("\n[Phase 3] Field Extraction")
    fields = FIELDS_BY_DOC_TYPE["purchase_agreement"]
    prompt = FIELD_EXTRACTOR_PROMPT.format(
        fields_json=json.dumps(fields, indent=2),
        text=SAMPLE_TEXT[:12000],
    )
    _, t = time_call("extract_fields(purchase_agreement)", claude_json, prompt, max_tokens=1024)
    timings["extract_fields_1_doc"] = t

    # ── Phase 3: Consistency checks (2 calls) ─────────────────────────
    print("\n[Consistency] CC-001 + CC-002")
    comparison = {
        "Buyer/borrower name": {
            "purchase_agreement (buyer_name)": "John A. Martinez",
            "loan_note (borrower_name)": "John Martinez",
            "mortgage_deed (borrower_name)": "John A. Martinez",
        }
    }
    prompt_cc = CONSISTENCY_CHECK_PROMPT.format(
        comparison_json=json.dumps(comparison, indent=2)
    )
    _, t = time_call("consistency_check CC-001", claude_json, prompt_cc)
    timings["consistency_cc001"] = t

    comparison2 = {
        "Property address": {
            "purchase_agreement": "4821 Clearwater Drive, Charlotte, NC 28210",
            "mortgage_deed": "4821 Clearwater Dr., Charlotte, NC 28210",
        }
    }
    prompt_cc2 = CONSISTENCY_CHECK_PROMPT.format(
        comparison_json=json.dumps(comparison2, indent=2)
    )
    _, t = time_call("consistency_check CC-002", claude_json, prompt_cc2)
    timings["consistency_cc002"] = t

    # ── Phase 4: Executive Brief ─────────────────────────────────────
    print("\n[Phase 5] Report Build — Executive Brief")
    prompt_eb = EXECUTIVE_BRIEF_PROMPT.format(
        rule_results_json=json.dumps(SAMPLE_RULE_RESULTS, indent=2)
    )
    _, t = time_call("executive_brief (max_tokens=1024)", claude_json, prompt_eb, max_tokens=1024)
    timings["executive_brief"] = t

    # ── Phase 5: Action Plan ─────────────────────────────────────────
    print("\n[Phase 5] Report Build — Action Plan")
    prompt_ap = ACTION_PLAN_PROMPT.format(
        conflicts_json=json.dumps(SAMPLE_CONFLICTS, indent=2)
    )
    _, t = time_call("action_plan (max_tokens=4096)", claude_json, prompt_ap, max_tokens=4096)
    timings["action_plan"] = t

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SUMMARY (single-doc job with 3 FAILs + 2 WARNINGs)")
    print("=" * 60)

    # Simulate a typical 5-document job
    n_docs = 5
    simulated = {
        "Ingestion (PDF parse × N)":             0.1 * n_docs,
        "Classification × N (sequential)":      timings["classify_1_doc"] * n_docs,
        "Field extraction × N (sequential)":    timings["extract_fields_1_doc"] * n_docs,
        "Consistency checks (CC-001 + CC-002)":  timings["consistency_cc001"] + timings["consistency_cc002"],
        "Rule engine (pure Python, no LLM)":     0.001,
        "Executive brief":                       timings["executive_brief"],
        "Action plan":                           timings["action_plan"],
    }

    total = sum(simulated.values())
    print(f"\n  {'Stage':<42} {'BEFORE':>8}  {'% of old':>9}  {'AFTER (parallel)':>18}")
    print(f"  {'-'*42}  {'-'*8}  {'-'*9}  {'-'*18}")
    optimized = {
        "Ingestion (PDF parse × N)":             0.1 * n_docs,
        "Classification × N (parallel)":         timings["classify_1_doc"],        # bottleneck → wall-clock = 1 call
        "Field extraction × N (parallel)":       timings["extract_fields_1_doc"],  # same
        "Consistency checks (parallel)":         max(timings["consistency_cc001"], timings["consistency_cc002"]),
        "Rule engine (pure Python, no LLM)":     0.001,
        "Executive brief + Action plan (parallel)": max(timings["executive_brief"], timings["action_plan"]),
    }
    opt_total = sum(optimized.values())
    opt_iter = iter(optimized.values())
    for stage, t in simulated.items():
        pct = t / total * 100
        flag = " ◄ BOTTLENECK" if pct > 25 else ""
        print(f"  {stage:<42} {t:>7.2f}s  {pct:>8.1f}%{flag}")
    print(f"\n  {'ESTIMATED TOTAL — BEFORE (5-doc job)':<42} {total:>7.2f}s")
    print(f"\n  {'Stage (after parallelization)':<42} {'AFTER':>8}")
    print(f"  {'-'*42}  {'-'*8}")
    for stage, t in optimized.items():
        print(f"  {stage:<42} {t:>7.2f}s")
    saving_pct = (total - opt_total) / total * 100
    print(f"\n  {'ESTIMATED TOTAL — AFTER (5-doc job)':<42} {opt_total:>7.2f}s  (−{saving_pct:.0f}%)")

    print("\n" + "=" * 60)
    print("  RAW SINGLE CALL TIMINGS")
    print("=" * 60)
    for k, v in timings.items():
        print(f"  {k:<40} {v:.2f}s")

    print()
    return timings


if __name__ == "__main__":
    run_benchmark()
