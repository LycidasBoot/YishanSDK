from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from models.access_event import AccessEvent
from models.core_page import CorePage
from services.ip_location_service import lookup_ip_locations

HIGH_INTENT_SCORE = 60
DEFAULT_WINDOW_DAYS = 30


def _window_start(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _active_core_pages(db: Session, site_id: int) -> list[CorePage]:
    return list(
        db.scalars(
            select(CorePage)
            .where(CorePage.site_id == site_id, CorePage.is_active.is_(True))
            .order_by(CorePage.priority.desc(), CorePage.id.asc())
        ).all()
    )


def _lead_score(request_count: int, core_page_hits: int, recent_hits: int) -> int:
    return min(100, request_count * 5 + core_page_hits * 20 + recent_hits * 15)


def _page_score(request_count: int, organization_count: int, core_page_hits: int) -> int:
    return min(100, request_count * 2 + organization_count * 18 + core_page_hits * 12)


def _lead_ip_context(db: Session, site_id: int, organization_name: str, since: datetime) -> dict:
    client_ips = list(
        db.scalars(
            select(AccessEvent.client_ip)
            .where(
                AccessEvent.site_id == site_id,
                AccessEvent.event_time >= since,
                AccessEvent.is_bot.is_(False),
                AccessEvent.organization_name == organization_name,
            )
            .distinct()
        ).all()
    )
    locations = lookup_ip_locations(client_ips)
    location_labels = sorted({item.location for item in locations.values() if item.location})
    owner_labels = sorted({item.network_owner for item in locations.values() if item.network_owner})
    return {
        "ip_count": len(client_ips),
        "locations": location_labels[:4],
        "network_owners": owner_labels[:4],
    }


def get_leads(db: Session, site_id: int, limit: int = 20, days: int = DEFAULT_WINDOW_DAYS) -> list[dict]:
    since = _window_start(days)
    recent_since = datetime.now(timezone.utc) - timedelta(hours=24)
    core_paths = [page.path for page in _active_core_pages(db, site_id)]

    stmt = (
        select(
            AccessEvent.organization_name.label("organization_name"),
            func.max(AccessEvent.organization_domain).label("organization_domain"),
            func.max(AccessEvent.organization_type).label("organization_type"),
            func.count(AccessEvent.id).label("request_count"),
            func.coalesce(
                func.sum(case((AccessEvent.normalized_path.in_(core_paths), 1), else_=0)) if core_paths else 0,
                0,
            ).label("core_page_hits"),
            func.coalesce(func.sum(case((AccessEvent.event_time >= recent_since, 1), else_=0)), 0).label("recent_hits"),
            func.max(AccessEvent.event_time).label("last_seen"),
        )
        .where(
            AccessEvent.site_id == site_id,
            AccessEvent.event_time >= since,
            AccessEvent.is_bot.is_(False),
            AccessEvent.organization_name.is_not(None),
        )
        .group_by(AccessEvent.organization_name)
        .order_by(desc("last_seen"))
    )
    rows = db.execute(stmt).all()
    leads = []
    for row in rows:
        request_count = int(row.request_count or 0)
        core_page_hits = int(row.core_page_hits or 0)
        recent_hits = int(row.recent_hits or 0)
        leads.append(
            {
                "organization_name": row.organization_name,
                "organization_domain": row.organization_domain,
                "organization_type": row.organization_type,
                "request_count": request_count,
                "core_page_hits": core_page_hits,
                "recent_hits": recent_hits,
                "last_seen": row.last_seen,
                "intent_score": _lead_score(request_count, core_page_hits, recent_hits),
                **_lead_ip_context(db, site_id, row.organization_name, since),
            }
        )
    return sorted(leads, key=lambda item: (item["intent_score"], item["last_seen"]), reverse=True)[:limit]


def get_crawler_coverage(db: Session, site_id: int, days: int = DEFAULT_WINDOW_DAYS) -> dict:
    since = _window_start(days)
    pages = _active_core_pages(db, site_id)
    page_rows = []

    for page in pages:
        stmt = select(
            func.coalesce(func.sum(case((AccessEvent.bot_category == "ai_bot", 1), else_=0)), 0).label("ai_hits"),
            func.coalesce(func.sum(case((AccessEvent.bot_category == "search_engine", 1), else_=0)), 0).label(
                "search_hits"
            ),
            func.max(case((AccessEvent.bot_category == "ai_bot", AccessEvent.event_time), else_=None)).label(
                "last_ai_seen"
            ),
            func.max(case((AccessEvent.bot_category == "search_engine", AccessEvent.event_time), else_=None)).label(
                "last_search_seen"
            ),
            func.coalesce(func.sum(case((AccessEvent.status >= 400, 1), else_=0)), 0).label("status_errors"),
        ).where(
            AccessEvent.site_id == site_id,
            AccessEvent.event_time >= since,
            AccessEvent.normalized_path == page.path,
        )
        row = db.execute(stmt).one()
        page_rows.append(
            {
                "path": page.path,
                "title": page.title,
                "category": page.category,
                "priority": page.priority,
                "ai_hits": int(row.ai_hits or 0),
                "search_hits": int(row.search_hits or 0),
                "last_ai_seen": row.last_ai_seen,
                "last_search_seen": row.last_search_seen,
                "status_errors": int(row.status_errors or 0),
            }
        )

    active_count = len(pages)
    ai_covered = sum(1 for row in page_rows if row["ai_hits"] > 0)
    search_covered = sum(1 for row in page_rows if row["search_hits"] > 0)
    return {
        "active_core_pages": active_count,
        "ai_covered_pages": ai_covered,
        "search_covered_pages": search_covered,
        "ai_coverage_ratio": round(ai_covered / active_count, 4) if active_count else 0,
        "search_coverage_ratio": round(search_covered / active_count, 4) if active_count else 0,
        "pages": page_rows,
    }


def get_page_value(db: Session, site_id: int, limit: int = 20, days: int = DEFAULT_WINDOW_DAYS) -> list[dict]:
    since = _window_start(days)
    core_paths = {page.path for page in _active_core_pages(db, site_id)}
    stmt = (
        select(
            AccessEvent.normalized_path.label("path"),
            func.count(AccessEvent.id).label("request_count"),
            func.count(func.distinct(AccessEvent.organization_name)).label("organization_count"),
            func.max(AccessEvent.event_time).label("last_seen"),
        )
        .where(
            AccessEvent.site_id == site_id,
            AccessEvent.event_time >= since,
            AccessEvent.is_bot.is_(False),
        )
        .group_by(AccessEvent.normalized_path)
        .order_by(desc("request_count"))
        .limit(limit * 3)
    )
    rows = db.execute(stmt).all()
    items = []
    for row in rows:
        request_count = int(row.request_count or 0)
        organization_count = int(row.organization_count or 0)
        core_page_hits = request_count if row.path in core_paths else 0
        items.append(
            {
                "path": row.path,
                "request_count": request_count,
                "organization_count": organization_count,
                "core_page_hits": core_page_hits,
                "last_seen": row.last_seen,
                "value_score": _page_score(request_count, organization_count, core_page_hits),
            }
        )
    return sorted(items, key=lambda item: (item["value_score"], item["request_count"]), reverse=True)[:limit]


def get_overview(db: Session, site_id: int, days: int = DEFAULT_WINDOW_DAYS) -> dict:
    since = _window_start(days)
    total_organizations = int(
        db.scalar(
            select(func.count(func.distinct(AccessEvent.organization_name))).where(
                AccessEvent.site_id == site_id,
                AccessEvent.event_time >= since,
                AccessEvent.is_bot.is_(False),
                AccessEvent.organization_name.is_not(None),
            )
        )
        or 0
    )
    ai_bot_requests = int(
        db.scalar(
            select(func.count(AccessEvent.id)).where(
                AccessEvent.site_id == site_id,
                AccessEvent.event_time >= since,
                AccessEvent.bot_category == "ai_bot",
            )
        )
        or 0
    )
    search_engine_requests = int(
        db.scalar(
            select(func.count(AccessEvent.id)).where(
                AccessEvent.site_id == site_id,
                AccessEvent.event_time >= since,
                AccessEvent.bot_category == "search_engine",
            )
        )
        or 0
    )
    leads = get_leads(db, site_id, limit=100, days=days)
    coverage = get_crawler_coverage(db, site_id, days=days)
    alert_count = 0
    alert_count += sum(1 for page in coverage["pages"] if page["ai_hits"] == 0)
    alert_count += sum(1 for page in coverage["pages"] if page["status_errors"] > 0)

    return {
        "total_organizations": total_organizations,
        "high_intent_organizations": sum(1 for lead in leads if lead["intent_score"] >= HIGH_INTENT_SCORE),
        "ai_bot_requests": ai_bot_requests,
        "search_engine_requests": search_engine_requests,
        "active_core_pages": coverage["active_core_pages"],
        "ai_covered_pages": coverage["ai_covered_pages"],
        "ai_coverage_ratio": coverage["ai_coverage_ratio"],
        "alert_count": alert_count,
    }


def get_crawler_name_counts(db: Session, site_id: int, days: int = DEFAULT_WINDOW_DAYS) -> list[dict]:
    since = _window_start(days)
    rows = db.execute(
        select(
            func.coalesce(AccessEvent.crawler_name, AccessEvent.bot_category).label("key"),
            func.count(AccessEvent.id).label("count"),
        )
        .where(AccessEvent.site_id == site_id, AccessEvent.event_time >= since, AccessEvent.is_bot.is_(True))
        .group_by("key")
        .order_by(desc("count"))
        .limit(12)
    ).all()
    return [{"key": str(row.key or ""), "count": int(row.count or 0)} for row in rows]


def get_anomaly_hints(db: Session, site_id: int, days: int = DEFAULT_WINDOW_DAYS) -> list[str]:
    since = _window_start(days)
    hints: list[str] = []
    script_count = int(
        db.scalar(
            select(func.count(AccessEvent.id)).where(
                AccessEvent.site_id == site_id,
                AccessEvent.event_time >= since,
                AccessEvent.bot_category == "script_client",
            )
        )
        or 0
    )
    if script_count:
        hints.append(f"最近 {days} 天发现 {script_count} 次脚本客户端访问")

    coverage = get_crawler_coverage(db, site_id, days=days)
    missing_ai = [page["path"] for page in coverage["pages"] if page["ai_hits"] == 0]
    if missing_ai:
        hints.append(f"{len(missing_ai)} 个核心页面最近 {days} 天未被 AI 爬虫抓取")

    errors_by_path = defaultdict(int)
    rows = db.execute(
        select(AccessEvent.normalized_path, func.count(AccessEvent.id))
        .where(AccessEvent.site_id == site_id, AccessEvent.event_time >= since, AccessEvent.status >= 400)
        .group_by(AccessEvent.normalized_path)
    ).all()
    for path, count in rows:
        errors_by_path[path] += int(count or 0)
    if errors_by_path:
        path, count = max(errors_by_path.items(), key=lambda item: item[1])
        hints.append(f"{path} 最近 {days} 天出现 {count} 次 4xx/5xx")

    return hints[:5]
