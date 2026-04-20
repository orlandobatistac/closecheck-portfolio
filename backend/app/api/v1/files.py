import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.job import JobStatus, ValidationJob

router = APIRouter()

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)


@router.get("/jobs/{job_id}/files/{filename}")
def get_job_file(job_id: str, filename: str, db: Session = Depends(get_db)):
    """
    Serve an original uploaded file for a completed job.
    Used by the split-view Document Viewer in the frontend.
    """
    if not _UUID_RE.match(job_id):
        raise HTTPException(400, "Invalid job ID format")

    job = db.query(ValidationJob).filter(ValidationJob.id == job_id).first()
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(409, f"Job '{job_id}' is not completed yet")

    upload_root = Path(settings.upload_dir).resolve()
    job_dir = (upload_root / job_id).resolve()
    file_path = (job_dir / filename).resolve()

    # Prevent path traversal: ensure the resolved path is inside the job directory
    try:
        file_path.relative_to(job_dir)
    except ValueError:
        raise HTTPException(400, "Invalid filename")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"File '{filename}' not found for job '{job_id}'")

    return FileResponse(
        path=str(file_path),
        media_type='application/pdf',
        content_disposition_type='inline',
    )
