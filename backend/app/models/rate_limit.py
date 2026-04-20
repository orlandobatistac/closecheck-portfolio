import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RateLimitEntry(Base):
    __tablename__ = "rate_limit_entries"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip_hash: Mapped[str] = mapped_column(String, index=True)
    device_token_hash: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
