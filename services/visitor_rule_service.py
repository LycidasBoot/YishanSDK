from sqlalchemy import select
from sqlalchemy.orm import Session

from models.visitor_identity_rule import VisitorIdentityRule
from schemas.visitor_rule import VisitorIdentityRuleCreate, VisitorIdentityRuleUpdate


def create_visitor_rule(db: Session, payload: VisitorIdentityRuleCreate) -> VisitorIdentityRule:
    rule = VisitorIdentityRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_visitor_rules(db: Session, active_only: bool = False) -> list[VisitorIdentityRule]:
    stmt = select(VisitorIdentityRule).order_by(VisitorIdentityRule.priority.desc(), VisitorIdentityRule.id.asc())
    if active_only:
        stmt = stmt.where(VisitorIdentityRule.is_active.is_(True))
    return list(db.scalars(stmt).all())


def update_visitor_rule(
    db: Session,
    rule_id: int,
    payload: VisitorIdentityRuleUpdate,
) -> VisitorIdentityRule | None:
    rule = db.get(VisitorIdentityRule, rule_id)
    if rule is None:
        return None

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule
