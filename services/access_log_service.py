from sqlalchemy.orm import Session

from detector import detect_bot
from models.access_event import AccessEvent
from models.site import Site
from parser import parse_access_log
from services.url_service import normalize_path
from services.visitor_identity_service import resolve_visitor_identity


def collect_access_log(db: Session, site_id: int, raw_log: str) -> AccessEvent:
    site = db.get(Site, site_id)
    if site is None:
        raise ValueError(f"site_id {site_id} does not exist")

    parsed = parse_access_log(raw_log)
    detection = detect_bot(parsed["user_agent"])
    identity = resolve_visitor_identity(db, parsed["client_ip"])
    event = AccessEvent(
        site_id=site_id,
        event_time=parsed["request_time"],
        client_ip=parsed["client_ip"],
        method=parsed["method"],
        path=parsed["path"],
        normalized_path=normalize_path(parsed["path"]),
        protocol=parsed["protocol"],
        status=parsed["status"],
        bytes_sent=parsed["bytes_sent"],
        referer=parsed["referer"],
        user_agent=parsed["user_agent"],
        is_bot=detection["is_bot"],
        bot_score=detection["bot_score"],
        bot_category=detection["bot_category"],
        crawler_name=detection["crawler_name"],
        risk_level=detection["risk_level"],
        hit_rules=detection["hit_rules"],
        organization_name=identity.organization_name if identity else None,
        organization_domain=identity.organization_domain if identity else None,
        organization_type=identity.organization_type if identity else None,
        organization_source=identity.organization_source if identity else None,
        organization_confidence=identity.organization_confidence if identity else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
