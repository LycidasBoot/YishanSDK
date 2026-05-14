from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SiteCreate(BaseModel):
    site_code: str
    site_name: str
    domain: str
    base_url: str
    status: str = "active"


class SiteRead(BaseModel):
    id: int
    site_code: str
    site_name: str
    domain: str
    base_url: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
