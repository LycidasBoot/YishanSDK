from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from models.session import get_db
from schemas.stats import CountItem, OverviewStats
from services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewStats)
def overview(site_id: int, db: Session = Depends(get_db)):
    return stats_service.get_overview(db, site_id)


@router.get("/bot-category", response_model=list[CountItem])
def bot_category(site_id: int, db: Session = Depends(get_db)):
    return stats_service.get_bot_category_counts(db, site_id)


@router.get("/top-ip", response_model=list[CountItem])
def top_ip(site_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return stats_service.get_top_ip(db, site_id, limit)


@router.get("/top-path", response_model=list[CountItem])
def top_path(site_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return stats_service.get_top_path(db, site_id, limit)


@router.get("/top-ua", response_model=list[CountItem])
def top_ua(site_id: int, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return stats_service.get_top_ua(db, site_id, limit)


@router.get("/export.csv")
def export_stats_csv(site_id: int, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    csv_content = stats_service.build_stats_export_csv(db, site_id, limit)
    filename = quote(f"crawler-stats-site-{site_id}.csv")
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
