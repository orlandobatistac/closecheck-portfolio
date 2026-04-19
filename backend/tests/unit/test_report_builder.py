"""Unit tests for report_builder — Day 6 suite.

Tests overall triage logic, conflicts extraction, documents status,
executive_brief, and action_plan behavior.
Claude calls are mocked with valid responses throughout.
"""
import pytest
from unittest.mock import patch

from app.llm.client import ClaudeResponseError
from app.rules.base import RuleResult, RuleStatus, Severity
from app.services.report_builder import build_report


# ── helpers ────────────────────────────────────────────────────────────────────

def _r(rule_id: str, status: RuleStatus, severity: Severity = Severity.FAIL,
        category: str = "purchase_agreement", detail: str = None,
        refs: list = None) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        category=category,
        description=f"Rule {rule_id}",
        severity=severity,
        status=status,
        detail=detail,
        documents_referenced=refs or [],
    )


_VALID_BRIEF = {"bullets": ["Issue A", "Issue B", "Issue C", "Issue D", "Issue E"]}
_VALID_PLAN  = [{"title": "Fix", "description": "x", "urgency": "now",
                 "owner": "coordinator", "is_blocker": True}]


def _mock_claude(brief=None, plan=None):
    """Patch Claude to return valid brief then valid plan (two sequential calls)."""
    return patch(
        "app.services.report_builder.claude_json",
        side_effect=[brief or _VALID_BRIEF, plan or _VALID_PLAN],
    )


# ── overall triage ─────────────────────────────────────────────────────────────

class TestOverall:
    def test_one_fail_gives_overall_fail(self):
        with _mock_claude():
            report = build_report([_r("PA-001", RuleStatus.FAIL)])
        assert report["overall"] == "FAIL"

    def test_warning_only_gives_overall_warning(self):
        with _mock_claude():
            report = build_report([
                _r("PA-005", RuleStatus.WARNING, Severity.WARNING),
                _r("PA-006", RuleStatus.PASS),
            ])
        assert report["overall"] == "WARNING"

    def test_all_pass_gives_overall_pass(self):
        # No Claude calls when no FAIL/WARNING results
        report = build_report([_r("PA-006", RuleStatus.PASS)])
        assert report["overall"] == "PASS"

    def test_summary_counts_are_correct(self):
        with _mock_claude():
            report = build_report([
                _r("PA-001", RuleStatus.FAIL),
                _r("PA-005", RuleStatus.WARNING, Severity.WARNING),
                _r("PA-006", RuleStatus.PASS),
                _r("PA-007", RuleStatus.PASS),
            ])
        assert report["summary"]["total_rules"] == 4
        assert report["summary"]["failed"] == 1
        assert report["summary"]["warnings"] == 1
        assert report["summary"]["passed"] == 2


# ── conflicts extraction ──────────────────────────────────────────────────────

class TestConflicts:
    def test_fail_rules_become_conflicts(self):
        with _mock_claude():
            report = build_report([_r("PA-003", RuleStatus.FAIL, detail="price mismatch")])
        assert len(report["conflicts"]) == 1
        assert report["conflicts"][0]["rule_id"] == "PA-003"
        assert report["conflicts"][0]["resolved"] is False

    def test_warning_rules_become_conflicts(self):
        with _mock_claude():
            report = build_report([
                _r("PA-005", RuleStatus.WARNING, Severity.WARNING, detail="no earnest money")
            ])
        assert len(report["conflicts"]) == 1

    def test_pass_rules_not_in_conflicts(self):
        report = build_report([_r("PA-006", RuleStatus.PASS)])
        assert report["conflicts"] == []

    def test_cross_doc_rule_gets_field_metadata(self):
        with _mock_claude():
            report = build_report(
                [_r("PA-003", RuleStatus.FAIL)],
                fields_by_doc={
                    "purchase_agreement": {"purchase_price": "$385,000"},
                    "closing_disclosure": {"purchase_price": "$387,500"},
                },
            )
        conflict = report["conflicts"][0]
        assert conflict["field"] == "purchase price"
        assert conflict["value_a"] == "$385,000"
        assert conflict["value_b"] == "$387,500"


# ── documents status ──────────────────────────────────────────────────────────

class TestDocuments:
    def test_classified_doc_with_no_issues_is_ok(self):
        report = build_report(
            [],
            classifications={
                "pa.pdf": {"document_type": "purchase_agreement", "confidence": 0.95}
            },
        )
        assert report["documents"][0]["status"] == "ok"

    def test_low_confidence_doc_is_warn(self):
        report = build_report(
            [],
            classifications={
                "unknown.pdf": {"document_type": "other", "confidence": 0.45}
            },
        )
        assert report["documents"][0]["status"] == "warn"


# ── executive_brief ───────────────────────────────────────────────────────────

class TestExecutiveBrief:
    def test_claude_bullets_returned(self):
        bullets = ["Issue A", "Issue B", "Issue C", "Issue D", "Issue E"]
        results = [_r("PA-001", RuleStatus.FAIL)]
        with _mock_claude(brief={"bullets": bullets}):
            report = build_report(results)
        assert report["executive_brief"] == bullets

    def test_raises_when_claude_returns_no_bullets(self):
        """Missing 'bullets' in response must raise — no silent fallback."""
        results = [_r("PA-001", RuleStatus.FAIL)]
        with patch("app.services.report_builder.claude_json", return_value={"something_else": []}):
            with pytest.raises(ClaudeResponseError, match="missing 'bullets' list"):
                build_report(results)

    def test_no_issues_gives_all_clear_without_claude(self):
        """All-pass jobs skip the Claude call and return a static message."""
        report = build_report([_r("PA-006", RuleStatus.PASS)])
        brief = report["executive_brief"]
        assert len(brief) == 1
        assert "ready" in brief[0].lower() or "passed" in brief[0].lower()


# ── action_plan ───────────────────────────────────────────────────────────────

class TestActionPlan:
    def test_no_issues_gives_empty_plan_without_claude(self):
        report = build_report([_r("PA-006", RuleStatus.PASS)])
        assert report["action_plan"] == []

    def test_claude_plan_returned(self):
        plan = [{"title": "Fix name", "description": "x", "urgency": "now",
                 "owner": "coordinator", "is_blocker": True}]
        with _mock_claude(plan=plan):
            report = build_report([_r("PA-001", RuleStatus.FAIL)])
        assert report["action_plan"] == plan

    def test_raises_when_claude_returns_invalid_plan(self):
        """Action plan with no recognizable structure must raise."""
        results = [_r("PA-001", RuleStatus.FAIL)]
        with patch(
            "app.services.report_builder.claude_json",
            side_effect=[_VALID_BRIEF, {"bad_key": "value"}],
        ):
            with pytest.raises(ClaudeResponseError, match="no recognizable key"):
                build_report(results)

