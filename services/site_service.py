from sqlalchemy import select
from sqlalchemy.orm import Session

from models.site import Site
from schemas.site import SiteCreate


def create_site(db: Session, payload: SiteCreate) -> Site:
    site = Site(**payload.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def list_sites(db: Session) -> list[Site]:
    return list(db.scalars(select(Site).order_by(Site.id.desc())).all())


def get_site(db: Session, site_id: int) -> Site | None:
    return db.get(Site, site_id)
