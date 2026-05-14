from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_requests: int
    bot_requests: int
    human_requests: int
    bot_ratio: float


class CountItem(BaseModel):
    key: str
    count: int
