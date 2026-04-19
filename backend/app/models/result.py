from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("validation_jobs.id"))
    rule_id: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String)   # FAIL | WARNING | INFO
    status: Mapped[str] = mapped_column(String)      # PASS | FAIL | WARNING | SKIPPED
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Stored as JSON string: '["file1.pdf", "file2.pdf"]'
    documents_referenced: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped["ValidationJob"] = relationship(  # noqa: F821
        "ValidationJob", back_populates="results"
    )
