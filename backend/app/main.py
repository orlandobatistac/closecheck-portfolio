from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.db.database import create_tables
from app.models import job, result  # noqa: F401 — register ORM models eagerly

app = FastAPI(
    title="CloseCheck API",
    description="AI Pre-Close File Validator for Real Estate",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    create_tables()


app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "closecheck-api", "version": "0.1.0"}
