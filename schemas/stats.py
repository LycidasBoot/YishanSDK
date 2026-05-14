from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_requests: int
    bot_requests: int
    human_requests: int
    bot_ratio: float


class CountItem(BaseModel):
    key: str
    count: int


class TopIpItem(CountItem):
    location: str | None = None
    network_owner: str | None = None
    organization_name: str | None = None
    organization_domain: str | None = None
