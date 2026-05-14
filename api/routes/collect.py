from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.session import get_db
from parser import NginxLogParseError
from schemas.access_log import AccessLogCollectRequest, AccessLogCollectResponse
from services.access_log_service import collect_access_log

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post("/access-log", response_model=AccessLogCollectResponse)
def collect(payload: AccessLogCollectRequest, db: Session = Depends(get_db)):
    try:
        event = collect_access_log(db, payload.site_id, payload.raw_log)
    except NginxLogParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AccessLogCollectResponse(
        event_id=event.id,
        site_id=event.site_id,
        event_time=event.event_time,
        client_ip=event.client_ip,
        path=event.path,
        normalized_path=event.normalized_path,
        user_agent=event.user_agent,
        is_bot=event.is_bot,
        bot_score=event.bot_score,
        bot_category=event.bot_category,
        crawler_name=event.crawler_name,
        risk_level=event.risk_level,
        hit_rules=event.hit_rules,
        organization_name=event.organization_name,
        organization_domain=event.organization_domain,
        organization_type=event.organization_type,
        organization_source=event.organization_source,
        organization_confidence=event.organization_confidence,
    )
