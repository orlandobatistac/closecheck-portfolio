from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Request ────────────────────────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    transaction_type: str = "residential"


class EmailDraftRequest(BaseModel):
    conflict_rule_id: str
    recipient: str = "lender"


# ── Response fragments ─────────────────────────────────────────────────────────

class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class RuleResultSchema(BaseModel):
    rule_id: str
    category: str
    description: str
    severity: str                               # FAIL | WARNING | INFO
    status: str                                 # PASS | FAIL | WARNING | SKIPPED
    detail: Optional[str] = None
    documents_referenced: Optional[list[str]] = None


class DocumentInfo(BaseModel):
    filename: str
    document_type: str
    confidence: float
    status: str = "ok"


class JobSummary(BaseModel):
    total_rules: int
    passed: int
    warnings: int
    failed: int


class ConflictCard(BaseModel):
    rule_id: str
    type: str
    severity: str
    message: str
    resolved: bool = False
    field: Optional[str] = None
    doc_a: Optional[str] = None
    value_a: Optional[str] = None
    doc_b: Optional[str] = None
    value_b: Optional[str] = None
    filename_a: Optional[str] = None   # actual uploaded filename for doc_a
    filename_b: Optional[str] = None   # actual uploaded filename for doc_b
    page_a: Optional[int] = None       # 1-indexed page where value_a was found
    page_b: Optional[int] = None       # 1-indexed page where value_b was found


class ActionItem(BaseModel):
    title: str
    description: str
    urgency: str                # now | today | soon
    owner: str                  # coordinator | lender | title | buyer | seller
    is_blocker: bool = False


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    overall: Optional[str] = None
    error_message: Optional[str] = None
    summary: Optional[JobSummary] = None
    documents: Optional[list[DocumentInfo]] = None
    results: Optional[list[RuleResultSchema]] = None
    conflicts: Optional[list[ConflictCard]] = None
    executive_brief: Optional[list[str]] = None
    action_plan: Optional[list[ActionItem]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmailDraftResponse(BaseModel):
    subject_pro: str
    body_pro: str
    subject_urg: str
    body_urg: str
