from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VisitorIdentityRuleCreate(BaseModel):
    rule_type: str
    pattern: str
    organization_name: str
    organization_domain: str | None = None
    organization_type: str = "company"
    confidence: int = Field(default=80, ge=0, le=100)
    priority: int = Field(default=100, ge=0, le=1000)
    is_active: bool = True


class VisitorIdentityRuleUpdate(BaseModel):
    rule_type: str | None = None
    pattern: str | None = None
    organization_name: str | None = None
    organization_domain: str | None = None
    organization_type: str | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)
    priority: int | None = Field(default=None, ge=0, le=1000)
    is_active: bool | None = None


class VisitorIdentityRuleRead(BaseModel):
    id: int
    rule_type: str
    pattern: str
    organization_name: str
    organization_domain: str | None
    organization_type: str
    confidence: int
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
