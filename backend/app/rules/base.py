"""Base class and shared types for all validation rules."""
import enum
from dataclasses import dataclass, field


class Severity(str, enum.Enum):
    FAIL = "FAIL"
    WARNING = "WARNING"
    INFO = "INFO"


class RuleStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class RuleResult:
    rule_id: str
    category: str
    description: str
    severity: Severity
    status: RuleStatus
    detail: str | None = None
    documents_referenced: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "detail": self.detail,
            "documents_referenced": self.documents_referenced,
        }


class BaseRule:
    """
    Subclass this for each rule. Override `check()`.
    `documents` is a dict keyed by document_type with extracted field dicts.
    """
    rule_id: str = ""
    category: str = ""
    description: str = ""
    severity: Severity = Severity.WARNING

    async def check(self, documents: dict) -> RuleResult:
        raise NotImplementedError

    def _pass(self, detail: str | None = None, refs: list[str] | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            description=self.description,
            severity=self.severity,
            status=RuleStatus.PASS,
            detail=detail,
            documents_referenced=refs or [],
        )

    def _fail(self, detail: str, refs: list[str] | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            description=self.description,
            severity=self.severity,
            status=RuleStatus.FAIL,
            detail=detail,
            documents_referenced=refs or [],
        )

    def _warning(self, detail: str, refs: list[str] | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            description=self.description,
            severity=self.severity,
            status=RuleStatus.WARNING,
            detail=detail,
            documents_referenced=refs or [],
        )

    def _skipped(self, reason: str = "Document not found") -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            description=self.description,
            severity=self.severity,
            status=RuleStatus.SKIPPED,
            detail=reason,
        )
