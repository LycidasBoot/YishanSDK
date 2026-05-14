from datetime import datetime

from pydantic import BaseModel


class IntelligenceOverview(BaseModel):
    total_organizations: int
    high_intent_organizations: int
    ai_bot_requests: int
    search_engine_requests: int
    active_core_pages: int
    ai_covered_pages: int
    ai_coverage_ratio: float
    alert_count: int


class LeadItem(BaseModel):
    organization_name: str
    organization_domain: str | None
    organization_type: str | None
    request_count: int
    core_page_hits: int
    recent_hits: int
    last_seen: datetime
    intent_score: int


class CrawlerCoveragePage(BaseModel):
    path: str
    title: str
    category: str
    priority: int
    ai_hits: int
    search_hits: int
    last_ai_seen: datetime | None
    last_search_seen: datetime | None
    status_errors: int


class CrawlerCoverage(BaseModel):
    active_core_pages: int
    ai_covered_pages: int
    search_covered_pages: int
    ai_coverage_ratio: float
    search_coverage_ratio: float
    pages: list[CrawlerCoveragePage]


class PageValueItem(BaseModel):
    path: str
    request_count: int
    organization_count: int
    core_page_hits: int
    last_seen: datetime
    value_score: int
