import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps.auth import verify_api_key
from app.api.deps.email_limit import check_email_draft_limit, record_email_draft
from app.api.deps.rate_limit import check_demo_rate_limit, record_rate_limit_entry
from app.api.deps.upload_rate_limit import check_upload_rate_limit, record_upload_attempt
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
    save_parsed_metadata,
    save_report,
    save_uploaded_files,
)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    # Existing
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Archives
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
    "application/octet-stream",   # browsers may report ZIP as this
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/tiff",
    "image/webp",
    "image/bmp",
    "image/x-bmp",
    # Web
    "text/html",
    "application/xhtml+xml",
    # Spreadsheets
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    # Delimited text
    "text/csv",
    "text/tab-separated-values",
    # Plain text
    "text/plain",
    # JSON
    "application/json",
    "text/json",
}


@router.post("/validate", response_model=JobCreateResponse, status_code=202)
async def validate_files(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    transaction_type: str = Form(default="residential"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """
    Accept a closing package (1–N files) and kick off async validation.
    Supported formats: PDF, DOCX, ZIP, images, HTML, XLSX, CSV, TXT, JSON.
    Returns a job_id to poll with GET /results/{job_id}.
    """
    if not files:
        raise HTTPException(400, "At least one file is required")

    if len(files) > settings.max_files_per_job:
        raise HTTPException(400, f"Maximum {settings.max_files_per_job} files per job")

    check_upload_rate_limit(request, db)
    check_demo_rate_limit(request, file_count=len(files), db=db)

    for f in files:
        if f.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                400,
                f"Unsupported content-type '{f.content_type}' for '{f.filename}'. "
                f"Supported formats: PDF, DOCX, ZIP, images (JPG/PNG/GIF/TIFF/BMP/WebP), "
                f"HTML, XLSX, CSV, TXT, JSON.",
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

    record_rate_limit_entry(request, file_count=len(files), db=db)
    record_upload_attempt(request, db)

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
        error_message=job.error_message,
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
    request: Request,
    body: EmailDraftRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
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

    check_email_draft_limit(job_id, request, db)

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
            model="claude-haiku-4-5",
        )
        conflict_type = conflict.get("type", "Issue")
        response = EmailDraftResponse(
            subject_pro=result.get("subject_pro", f"Action Required: {conflict_type}"),
            body_pro=result.get("body_pro", "Please review the attached conflict and respond promptly."),
            subject_urg=result.get("subject_urg", f"URGENT: {conflict_type} — Closing at Risk"),
            body_urg=result.get("body_urg", "Urgent attention required. Please respond immediately."),
        )
        record_email_draft(job_id, request, db)
        return response
    except HTTPException:
        raise
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

        # Phase 1: persist → expand ZIPs → dedup → type-detect → extract
        t0 = time.perf_counter()
        from pathlib import Path as _Path
        from app.services.zip_handler import expand_zips
        from app.services.file_type_detector import detect_file_type
        from app.services.deduplication import deduplicate
        from app.services.extractors import extract_document

        job_dir = _Path(settings.upload_dir) / job_id
        raw_paths = save_uploaded_files(job_id, file_payloads)

        # Expand any ZIP archives (recursive, ZIP-Slip safe)
        flat_paths, zip_warnings = expand_zips(raw_paths, job_dir)
        for w in zip_warnings:
            logger.warning("[%s] ZIP: %s", job_id, w)

        # Enforce file count limit post-expansion
        if len(flat_paths) > settings.max_files_per_job:
            raise ValueError(
                f"ZIP expansion yielded {len(flat_paths)} files which exceeds the "
                f"limit of {settings.max_files_per_job} files per job."
            )

        # Deduplicate by SHA-256
        flat_paths, dedup_warnings = deduplicate(flat_paths)
        for w in dedup_warnings:
            logger.info("[%s] Dedup: %s", job_id, w)

        # Detect type + extract each file; tolerate individual failures
        extracted: dict[str, str] = {}
        parsed_metadata: dict[str, dict] = {}
        all_ingestion_warnings: list[str] = []

        for path in flat_paths:
            file_type = detect_file_type(path)
            logger.info("[%s] Detected '%s' → type=%s", job_id, path.name, file_type)

            if file_type == "unknown":
                all_ingestion_warnings.append(
                    f"Skipped '{path.name}': file type could not be determined."
                )
                continue

            doc = extract_document(path, file_type)
            extracted[path.name] = doc.text
            parsed_metadata[path.name] = {
                "file_type":          doc.file_type,
                "extraction_method":  doc.extraction_method,
                "sha256":             doc.sha256,
                "source_archive":     doc.source_archive,
                "warnings":           doc.warnings,
                "metadata":           doc.metadata,
            }
            if doc.warnings:
                for w in doc.warnings:
                    logger.warning("[%s] %s: %s", job_id, path.name, w)

        save_extracted_texts(job_id, extracted)
        save_parsed_metadata(job_id, parsed_metadata)
        logger.info(
            "[%s] Ingestion complete in %.2fs (%d files, %d skipped)",
            job_id, time.perf_counter() - t0, len(extracted),
            len(flat_paths) - len(extracted),
        )

        # Phase 2: classify each document — all docs in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed
        t0 = time.perf_counter()
        classifications: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=min(len(extracted), 8)) as pool:
            future_to_file = {
                pool.submit(classify_document, text): filename
                for filename, text in extracted.items()
            }
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                result = future.result()  # propagates exceptions
                classifications[filename] = {
                    "document_type": result.document_type,
                    "confidence": result.confidence,
                    "notes": result.notes,
                }
                logger.info("Classified %s → %s (%.0f%%)", filename, result.document_type, result.confidence * 100)
        save_classifications(job_id, classifications)
        logger.info("[%s] Classification complete in %.2fs", job_id, time.perf_counter() - t0)

        # Phase 3: extract fields per document type — all doc types in parallel
        t0 = time.perf_counter()
        fields: dict[str, dict] = {}
        extract_tasks = {
            info["document_type"]: (filename, extracted.get(filename, ""))
            for filename, info in classifications.items()
            if info["document_type"] != "other"
        }
        with ThreadPoolExecutor(max_workers=min(len(extract_tasks), 8)) as pool:
            future_to_doctype = {
                pool.submit(extract_fields, doc_type, text): (doc_type, filename)
                for doc_type, (filename, text) in extract_tasks.items()
            }
            for future in as_completed(future_to_doctype):
                doc_type, filename = future_to_doctype[future]
                fields[doc_type] = future.result()
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

        # Build page_texts_by_doc: doc_type → list[str] (one string per page).
        # Only native PDFs carry page_texts; OCR docs have an empty list.
        page_texts_by_doc: dict[str, list[str]] = {}
        for fname, info in classifications.items():
            doc_type = info.get("document_type")
            if not doc_type or doc_type == "other":
                continue
            texts = (
                parsed_metadata
                .get(fname, {})
                .get("metadata", {})
                .get("page_texts", [])
            )
            if texts:
                page_texts_by_doc[doc_type] = texts

        report = build_report(
            all_results,
            fields_by_doc=fields,
            classifications=classifications,
            page_texts_by_doc=page_texts_by_doc,
        )
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


@router.post("/demo", response_model=JobCreateResponse, status_code=202)
async def run_demo(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Run a validation job using the bundled Martinez sample closing package."""
    from pathlib import Path as _Path
    sample_dir = _Path(__file__).parents[4] / "sample-docs" / "Martinez_test"
    sample_files = sorted(sample_dir.glob("*.pdf"))
    if not sample_files:
        raise HTTPException(status_code=500, detail="Sample demo files not found on server")

    check_demo_rate_limit(request, file_count=len(sample_files), db=db)

    job = ValidationJob(
        id=str(uuid.uuid4()),
        status=JobStatus.PENDING,
        transaction_type="residential",
        file_count=len(sample_files),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    record_rate_limit_entry(request, file_count=len(sample_files), db=db)

    file_payloads = [(f.name, f.read_bytes()) for f in sample_files]
    background_tasks.add_task(_process_job, job.id, file_payloads)
    return JobCreateResponse(job_id=job.id, status=job.status, created_at=job.created_at)
