from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CorePageCreate(BaseModel):
    site_id: int
    path: str
    title: str
    category: str = "general"
    priority: int = Field(default=50, ge=0, le=100)
    is_active: bool = True


class CorePageUpdate(BaseModel):
    path: str | None = None
    title: str | None = None
    category: str | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class CorePageRead(BaseModel):
    id: int
    site_id: int
    path: str
    title: str
    category: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
