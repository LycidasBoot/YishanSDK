from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.session import get_db
from schemas.visitor_rule import VisitorIdentityRuleCreate, VisitorIdentityRuleRead, VisitorIdentityRuleUpdate
from services import visitor_rule_service

router = APIRouter(prefix="/visitor-rules", tags=["visitor-rules"])


@router.post("", response_model=VisitorIdentityRuleRead)
def create_visitor_rule(payload: VisitorIdentityRuleCreate, db: Session = Depends(get_db)):
    try:
        return visitor_rule_service.create_visitor_rule(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="visitor rule already exists") from exc


@router.get("", response_model=list[VisitorIdentityRuleRead])
def list_visitor_rules(active_only: bool = Query(False), db: Session = Depends(get_db)):
    return visitor_rule_service.list_visitor_rules(db, active_only)


@router.patch("/{rule_id}", response_model=VisitorIdentityRuleRead)
def update_visitor_rule(rule_id: int, payload: VisitorIdentityRuleUpdate, db: Session = Depends(get_db)):
    try:
        rule = visitor_rule_service.update_visitor_rule(db, rule_id, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="visitor rule already exists") from exc
    if rule is None:
        raise HTTPException(status_code=404, detail="visitor rule not found")
    return rule
