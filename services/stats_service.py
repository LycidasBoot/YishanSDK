import csv
from io import StringIO

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from models.access_event import AccessEvent


def get_overview(db: Session, site_id: int) -> dict:
    stmt = select(
        func.count(AccessEvent.id).label("total_requests"),
        func.coalesce(func.sum(case((AccessEvent.is_bot.is_(True), 1), else_=0)), 0).label("bot_requests"),
    ).where(AccessEvent.site_id == site_id)
    row = db.execute(stmt).one()
    total_requests = int(row.total_requests or 0)
    bot_requests = int(row.bot_requests or 0)
    human_requests = total_requests - bot_requests
    bot_ratio = round(bot_requests / total_requests, 4) if total_requests else 0
    return {
        "total_requests": total_requests,
        "bot_requests": bot_requests,
        "human_requests": human_requests,
        "bot_ratio": bot_ratio,
    }


def count_by_field(db: Session, site_id: int, field, limit: int | None = None) -> list[dict]:
    stmt = (
        select(field.label("key"), func.count(AccessEvent.id).label("count"))
        .where(AccessEvent.site_id == site_id)
        .group_by(field)
        .order_by(desc("count"))
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = db.execute(stmt).all()
    return [{"key": str(row.key or ""), "count": int(row.count)} for row in rows]


def get_bot_category_counts(db: Session, site_id: int) -> list[dict]:
    return count_by_field(db, site_id, AccessEvent.bot_category)


def get_top_ip(db: Session, site_id: int, limit: int) -> list[dict]:
    return count_by_field(db, site_id, AccessEvent.client_ip, limit)


def get_top_path(db: Session, site_id: int, limit: int) -> list[dict]:
    return count_by_field(db, site_id, AccessEvent.path, limit)


def get_top_ua(db: Session, site_id: int, limit: int) -> list[dict]:
    return count_by_field(db, site_id, AccessEvent.user_agent, limit)


def build_stats_export_csv(db: Session, site_id: int, limit: int = 50) -> str:
    output = StringIO()
    writer = csv.writer(output)

    overview = get_overview(db, site_id)
    writer.writerow(["Crawler Stats SDK Export"])
    writer.writerow(["site_id", site_id])
    writer.writerow([])

    writer.writerow(["Overview"])
    writer.writerow(["total_requests", "bot_requests", "human_requests", "bot_ratio"])
    writer.writerow(
        [
            overview["total_requests"],
            overview["bot_requests"],
            overview["human_requests"],
            overview["bot_ratio"],
        ]
    )
    writer.writerow([])

    sections = [
        ("Bot Category", get_bot_category_counts(db, site_id)),
        ("Top IP", get_top_ip(db, site_id, limit)),
        ("Top URL Path", get_top_path(db, site_id, limit)),
        ("Top User-Agent", get_top_ua(db, site_id, limit)),
    ]
    for title, rows in sections:
        writer.writerow([title])
        writer.writerow(["key", "count"])
        for row in rows:
            writer.writerow([row["key"], row["count"]])
        writer.writerow([])

    return "\ufeff" + output.getvalue()
