from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class AccessEvent(Base):
    __tablename__ = "access_event"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), index=True, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    client_ip: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    normalized_path: Mapped[str] = mapped_column(Text, index=True, nullable=False, default="/")
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    bytes_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    referer: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=False)
    bot_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bot_category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    crawler_name: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    hit_rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    organization_name: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    organization_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_type: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    organization_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    organization_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    site = relationship("Site", back_populates="access_events")
