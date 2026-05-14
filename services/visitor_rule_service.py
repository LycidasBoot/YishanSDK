from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.access_event import AccessEvent
from models.visitor_identity_rule import VisitorIdentityRule
from schemas.visitor_rule import VisitorIdentityRuleCreate, VisitorIdentityRuleUpdate
from services.visitor_identity_service import _matches_rule


def _matching_ips_for_rule(rule: VisitorIdentityRule, client_ips: list[str]) -> list[str]:
    return [client_ip for client_ip in client_ips if _matches_rule(rule, client_ip)]


def apply_visitor_rule_to_events(db: Session, rule: VisitorIdentityRule) -> int:
    if not rule.is_active:
        return 0

    rule_type = rule.rule_type.lower()
    matched_ips: list[str]
    if rule_type in {"ip", "exact_ip"}:
        matched_ips = [rule.pattern.strip()]
    elif rule_type == "cidr":
        client_ips = list(db.scalars(select(AccessEvent.client_ip).distinct()).all())
        matched_ips = _matching_ips_for_rule(rule, client_ips)
    else:
        return 0

    if not matched_ips:
        return 0

    result = db.execute(
        update(AccessEvent)
        .where(AccessEvent.client_ip.in_(matched_ips))
        .values(
            organization_name=rule.organization_name,
            organization_domain=rule.organization_domain,
            organization_type=rule.organization_type,
            organization_source="local_rule",
            organization_confidence=rule.confidence,
        )
    )
    return int(result.rowcount or 0)


def create_visitor_rule(db: Session, payload: VisitorIdentityRuleCreate) -> VisitorIdentityRule:
    rule = VisitorIdentityRule(**payload.model_dump())
    db.add(rule)
    db.flush()
    apply_visitor_rule_to_events(db, rule)
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
    db.flush()
    apply_visitor_rule_to_events(db, rule)
    db.commit()
    db.refresh(rule)
    return rule
