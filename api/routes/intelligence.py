from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.session import get_db
from schemas.intelligence import CrawlerCoverage, IntelligenceOverview, LeadItem, PageValueItem
from schemas.stats import CountItem
from services import intelligence_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/overview", response_model=IntelligenceOverview)
def overview(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_overview(db, site_id, days)


@router.get("/leads", response_model=list[LeadItem])
def leads(
    site_id: int,
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_leads(db, site_id, limit, days)


@router.get("/crawler-coverage", response_model=CrawlerCoverage)
def crawler_coverage(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_crawler_coverage(db, site_id, days)


@router.get("/page-value", response_model=list[PageValueItem])
def page_value(
    site_id: int,
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_page_value(db, site_id, limit, days)


@router.get("/crawler-names", response_model=list[CountItem])
def crawler_names(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_crawler_name_counts(db, site_id, days)


@router.get("/anomaly-hints", response_model=list[str])
def anomaly_hints(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return intelligence_service.get_anomaly_hints(db, site_id, days)
