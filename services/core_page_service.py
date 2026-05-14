from sqlalchemy import select
from sqlalchemy.orm import Session

from models.core_page import CorePage
from models.site import Site
from schemas.core_page import CorePageCreate, CorePageUpdate
from services.url_service import normalize_path


def create_core_page(db: Session, payload: CorePageCreate) -> CorePage:
    if db.get(Site, payload.site_id) is None:
        raise ValueError(f"site_id {payload.site_id} does not exist")

    data = payload.model_dump()
    data["path"] = normalize_path(data["path"])
    page = CorePage(**data)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def list_core_pages(db: Session, site_id: int | None = None, active_only: bool = False) -> list[CorePage]:
    stmt = select(CorePage).order_by(CorePage.priority.desc(), CorePage.id.asc())
    if site_id is not None:
        stmt = stmt.where(CorePage.site_id == site_id)
    if active_only:
        stmt = stmt.where(CorePage.is_active.is_(True))
    return list(db.scalars(stmt).all())


def update_core_page(db: Session, page_id: int, payload: CorePageUpdate) -> CorePage | None:
    page = db.get(CorePage, page_id)
    if page is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    if "path" in data and data["path"] is not None:
        data["path"] = normalize_path(data["path"])
    for key, value in data.items():
        setattr(page, key, value)
    db.commit()
    db.refresh(page)
    return page
