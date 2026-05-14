from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AccessLogCollectRequest(BaseModel):
    site_id: int
    raw_log: str


class AccessLogCollectResponse(BaseModel):
    event_id: int
    site_id: int
    event_time: datetime
    client_ip: str
    path: str
    normalized_path: str
    user_agent: str | None
    is_bot: bool
    bot_score: int
    bot_category: str
    crawler_name: str | None
    risk_level: str
    hit_rules: list[dict[str, Any]]
    organization_name: str | None
    organization_domain: str | None
    organization_type: str | None
    organization_source: str | None
    organization_confidence: int | None
