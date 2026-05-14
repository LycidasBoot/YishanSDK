from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.session import get_db
from schemas.core_page import CorePageCreate, CorePageRead, CorePageUpdate
from services import core_page_service

router = APIRouter(prefix="/core-pages", tags=["core-pages"])


@router.post("", response_model=CorePageRead)
def create_core_page(payload: CorePageCreate, db: Session = Depends(get_db)):
    try:
        return core_page_service.create_core_page(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="core page path already exists for this site") from exc


@router.get("", response_model=list[CorePageRead])
def list_core_pages(
    site_id: int | None = None,
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return core_page_service.list_core_pages(db, site_id, active_only)


@router.patch("/{page_id}", response_model=CorePageRead)
def update_core_page(page_id: int, payload: CorePageUpdate, db: Session = Depends(get_db)):
    try:
        page = core_page_service.update_core_page(db, page_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="core page path already exists for this site") from exc
    if page is None:
        raise HTTPException(status_code=404, detail="core page not found")
    return page
