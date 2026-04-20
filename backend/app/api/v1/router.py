from fastapi import APIRouter

from app.api.v1 import files, reports, validate

router = APIRouter()
router.include_router(validate.router, tags=["validation"])
router.include_router(reports.router, tags=["reports"])
router.include_router(files.router, tags=["files"])


@router.get("/health", tags=["meta"])
def health_v1():
    return {"status": "ok", "service": "closecheck-api", "version": "0.1.0"}
