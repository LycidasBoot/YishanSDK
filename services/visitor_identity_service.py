from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.visitor_enrichment_cache import VisitorEnrichmentCache
from models.visitor_identity_rule import VisitorIdentityRule


@dataclass(frozen=True)
class VisitorIdentity:
    organization_name: str
    organization_domain: str | None
    organization_type: str
    organization_source: str
    organization_confidence: int


class VisitorIdentityProvider(Protocol):
    def lookup(self, client_ip: str) -> VisitorIdentity | None:
        pass


class NullVisitorIdentityProvider:
    def lookup(self, client_ip: str) -> VisitorIdentity | None:
        return None


def _matches_rule(rule: VisitorIdentityRule, client_ip: str) -> bool:
    rule_type = rule.rule_type.lower()
    pattern = rule.pattern.strip()

    if rule_type in {"ip", "exact_ip"}:
        return client_ip == pattern

    if rule_type == "cidr":
        try:
            return ip_address(client_ip) in ip_network(pattern, strict=False)
        except ValueError:
            return False

    return False


def _identity_from_rule(rule: VisitorIdentityRule) -> VisitorIdentity:
    return VisitorIdentity(
        organization_name=rule.organization_name,
        organization_domain=rule.organization_domain,
        organization_type=rule.organization_type,
        organization_source="local_rule",
        organization_confidence=rule.confidence,
    )


def _identity_from_cache(cache: VisitorEnrichmentCache) -> VisitorIdentity | None:
    if not cache.organization_name:
        return None
    return VisitorIdentity(
        organization_name=cache.organization_name,
        organization_domain=cache.organization_domain,
        organization_type=cache.organization_type or "company",
        organization_source=cache.organization_source,
        organization_confidence=cache.organization_confidence or 0,
    )


def resolve_visitor_identity(
    db: Session,
    client_ip: str,
    provider: VisitorIdentityProvider | None = None,
) -> VisitorIdentity | None:
    rules = db.scalars(
        select(VisitorIdentityRule)
        .where(VisitorIdentityRule.is_active.is_(True))
        .order_by(VisitorIdentityRule.priority.desc(), VisitorIdentityRule.id.asc())
    ).all()
    for rule in rules:
        if _matches_rule(rule, client_ip):
            return _identity_from_rule(rule)

    cache = db.scalar(select(VisitorEnrichmentCache).where(VisitorEnrichmentCache.client_ip == client_ip))
    cached_identity = _identity_from_cache(cache) if cache else None
    if cached_identity:
        return cached_identity

    identity = (provider or NullVisitorIdentityProvider()).lookup(client_ip)
    if identity:
        db.add(
            VisitorEnrichmentCache(
                client_ip=client_ip,
                organization_name=identity.organization_name,
                organization_domain=identity.organization_domain,
                organization_type=identity.organization_type,
                organization_source=identity.organization_source,
                organization_confidence=identity.organization_confidence,
                raw_payload={},
            )
        )
    return identity
