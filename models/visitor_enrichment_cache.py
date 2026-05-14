from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class VisitorEnrichmentCache(Base):
    __tablename__ = "visitor_enrichment_cache"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_ip: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    organization_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_type: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    organization_source: Mapped[str] = mapped_column(String(64), nullable=False, default="external")
    organization_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
