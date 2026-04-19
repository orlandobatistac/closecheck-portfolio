from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.job import JobStatus, ValidationJob
from app.services.ingestion import load_report
from app.services.pdf_generator import generate_pdf

router = APIRouter()


@router.get("/report/{job_id}/pdf")
def get_report_pdf(job_id: str, db: Session = Depends(get_db)):
    """
    Stream the PDF validation report for a completed job.
    Generates the PDF on first request and caches it for subsequent calls.
    """
    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(409, f"Job '{job_id}' is not completed yet (status: {job.status})")

    pdf_filename = f"CloseCheck_{job_id[:8]}.pdf"
    pdf_path = Path(settings.reports_dir) / pdf_filename

    if not pdf_path.exists():
        report = load_report(job_id)
        if not report:
            raise HTTPException(404, "Report data not found for this job")
        generate_pdf(report, str(pdf_path), job_id=job_id)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_filename,
    )
