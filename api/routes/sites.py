from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.session import get_db
from schemas.site import SiteCreate, SiteRead
from services import site_service

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=SiteRead)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    try:
        return site_service.create_site(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="site_code already exists") from exc


@router.get("", response_model=list[SiteRead])
def list_sites(db: Session = Depends(get_db)):
    return site_service.list_sites(db)


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = site_service.get_site(db, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="site not found")
    return site
