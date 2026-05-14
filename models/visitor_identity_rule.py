from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class VisitorIdentityRule(Base):
    __tablename__ = "visitor_identity_rule"
    __table_args__ = (UniqueConstraint("rule_type", "pattern", name="uq_visitor_identity_rule_type_pattern"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    pattern: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    organization_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    organization_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="company")
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    priority: Mapped[int] = mapped_column(Integer, index=True, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
