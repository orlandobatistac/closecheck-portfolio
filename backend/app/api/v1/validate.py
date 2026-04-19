import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.job import JobStatus, ValidationJob
from app.models.schemas import (
    ActionItem, ConflictCard, DocumentInfo, EmailDraftRequest, EmailDraftResponse,
    JobCreateResponse, JobResultResponse, JobSummary, RuleResultSchema,
)
from app.services.ingestion import (
    load_classifications,
    load_fields,
    load_report,
    save_classifications,
    save_extracted_texts,
    save_fields,
    save_report,
    save_uploaded_files,
)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/validate", response_model=JobCreateResponse, status_code=202)
async def validate_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    transaction_type: str = Form(default="residential"),
    db: Session = Depends(get_db),
):
    """
    Accept a closing package (1–N PDF/DOCX files) and kick off async validation.
    Returns a job_id to poll with GET /results/{job_id}.
    """
    if not files:
        raise HTTPException(400, "At least one file is required")

    if len(files) > settings.max_files_per_job:
        raise HTTPException(400, f"Maximum {settings.max_files_per_job} files per job")

    for f in files:
        if f.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                400,
                f"Unsupported file type for '{f.filename}'. Only PDF and DOCX are allowed.",
            )

    job = ValidationJob(
        id=str(uuid.uuid4()),
        status=JobStatus.PENDING,
        transaction_type=transaction_type,
        file_count=len(files),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    file_payloads: list[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        file_payloads.append((f.filename or "unnamed", content))

    background_tasks.add_task(_process_job, job.id, file_payloads)

    return JobCreateResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/results/{job_id}", response_model=JobResultResponse)
def get_results(job_id: str, db: Session = Depends(get_db)):
    """Poll job status and retrieve validation results once completed."""
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")

    documents: list[DocumentInfo] = []
    classifications = load_classifications(job_id)
    for filename, info in classifications.items():
        documents.append(DocumentInfo(
            filename=filename,
            document_type=info.get("document_type", "other"),
            confidence=info.get("confidence", 0.0),
        ))

    report = load_report(job_id)
    summary_data = report.get("summary")
    summary = JobSummary(**summary_data) if summary_data else None
    raw_results = report.get("results", [])
    results = [RuleResultSchema(**r) for r in raw_results] if raw_results else []
    raw_conflicts = report.get("conflicts", [])
    conflicts = [ConflictCard(**c) for c in raw_conflicts] if raw_conflicts else []
    raw_actions = report.get("action_plan", [])
    action_plan = [ActionItem(**a) for a in raw_actions] if raw_actions else []

    return JobResultResponse(
        job_id=job.id,
        status=job.status,
        overall=job.overall,
        created_at=job.created_at,
        completed_at=job.completed_at,
        documents=documents,
        results=results,
        summary=summary,
        conflicts=conflicts,
        executive_brief=report.get("executive_brief"),
        action_plan=action_plan,
    )


@router.post("/jobs/{job_id}/draft-email", response_model=EmailDraftResponse)
def draft_email(
    job_id: str,
    body: EmailDraftRequest,
    db: Session = Depends(get_db),
):
    """Generate a professional email draft for a specific conflict in a job."""
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")

    report = load_report(job_id)
    conflicts = report.get("conflicts", [])
    conflict = next(
        (c for c in conflicts if c.get("rule_id") == body.conflict_rule_id), None
    )
    if not conflict:
        raise HTTPException(
            404, f"Conflict '{body.conflict_rule_id}' not found in job report"
        )

    from app.llm.client import claude_json
    from app.llm.prompts import EMAIL_DRAFT_PROMPT
    import json

    try:
        result = claude_json(
            EMAIL_DRAFT_PROMPT.format(
                conflict_json=json.dumps(conflict, indent=2),
                recipient=body.recipient,
            ),
            max_tokens=1024,
        )
        conflict_type = conflict.get("type", "Issue")
        return EmailDraftResponse(
            subject_pro=result.get("subject_pro", f"Action Required: {conflict_type}"),
            body_pro=result.get("body_pro", "Please review the attached conflict and respond promptly."),
            subject_urg=result.get("subject_urg", f"URGENT: {conflict_type} — Closing at Risk"),
            body_urg=result.get("body_urg", "Urgent attention required. Please respond immediately."),
        )
    except Exception as exc:
        raise HTTPException(502, f"Email draft generation failed: {exc}")


# ── Background task ────────────────────────────────────────────────────────────

def _process_job(job_id: str, file_payloads: list[tuple[str, bytes]]) -> None:
    import asyncio
    import logging
    import time
    from app.db.database import SessionLocal
    from app.services.classifier import classify_document
    from app.services.consistency import run_consistency_checks
    from app.services.extractor import extract_fields
    from app.services.parser import extract_text
    from app.services.report_builder import build_report
    from app.services.validator import run_all_rules

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    t_start = time.perf_counter()

    def _elapsed() -> str:
        return f"{time.perf_counter() - t_start:.2f}s"

    try:
        job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING
        db.commit()
        logger.info("[%s] Job started", job_id)

        # Phase 1: persist + OCR
        t0 = time.perf_counter()
        saved_paths = save_uploaded_files(job_id, file_payloads)
        extracted: dict[str, str] = {}
        for path in saved_paths:
            extracted[path.name] = extract_text(path)
        save_extracted_texts(job_id, extracted)
        logger.info("[%s] OCR complete in %.2fs (%d files)", job_id, time.perf_counter() - t0, len(extracted))

        # Phase 2: classify each document
        t0 = time.perf_counter()
        classifications: dict[str, dict] = {}
        for filename, text in extracted.items():
            result = classify_document(text)
            classifications[filename] = {
                "document_type": result.document_type,
                "confidence": result.confidence,
                "notes": result.notes,
            }
            logger.info("Classified %s → %s (%.0f%%)", filename, result.document_type, result.confidence * 100)
        save_classifications(job_id, classifications)
        logger.info("[%s] Classification complete in %.2fs", job_id, time.perf_counter() - t0)

        # Phase 3: extract fields per document type
        t0 = time.perf_counter()
        fields: dict[str, dict] = {}
        for filename, info in classifications.items():
            doc_type = info["document_type"]
            if doc_type == "other":
                continue
            text = extracted.get(filename, "")
            fields[doc_type] = extract_fields(doc_type, text)
            logger.info("Extracted fields for %s (%s)", filename, doc_type)
        save_fields(job_id, fields)
        logger.info("[%s] Field extraction complete in %.2fs", job_id, time.perf_counter() - t0)

        # Phase 4: rule engine
        t0 = time.perf_counter()
        rule_results = asyncio.run(run_all_rules(fields))
        consistency_results = run_consistency_checks(fields)
        logger.info("[%s] Rules complete in %.2fs (%d results)", job_id, time.perf_counter() - t0, len(rule_results) + len(consistency_results))

        # Phase 5: build report
        t0 = time.perf_counter()
        all_results = rule_results + consistency_results
        report = build_report(all_results, fields_by_doc=fields, classifications=classifications)
        save_report(job_id, report)
        logger.info("[%s] Report built in %.2fs", job_id, time.perf_counter() - t0)

        job.status = JobStatus.COMPLETED
        job.overall = report["overall"]
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info("[%s] Job completed in %s — overall=%s", job_id, _elapsed(), report["overall"])

    except Exception as exc:
        logger.exception("Job %s failed after %s: %s", job_id, _elapsed(), exc)
        job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            db.commit()
    finally:
        db.close()
