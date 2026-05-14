from types import SimpleNamespace

from services.intelligence_service import _lead_score, _page_score
from services.url_service import normalize_path
from services.visitor_identity_service import _matches_rule
from services.visitor_rule_service import _matching_ips_for_rule


def test_normalize_path_removes_query_string():
    assert normalize_path("/products?utm_source=ad") == "/products"
    assert normalize_path("https://www.example.com/cases?a=1") == "/cases"
    assert normalize_path("") == "/"


def test_local_visitor_rule_matches_exact_ip():
    rule = SimpleNamespace(rule_type="exact_ip", pattern="203.0.113.10")

    assert _matches_rule(rule, "203.0.113.10") is True
    assert _matches_rule(rule, "203.0.113.11") is False


def test_local_visitor_rule_matches_cidr():
    rule = SimpleNamespace(rule_type="cidr", pattern="203.0.113.0/24")

    assert _matches_rule(rule, "203.0.113.10") is True
    assert _matches_rule(rule, "198.51.100.10") is False


def test_matching_ips_for_rule_filters_cidr():
    rule = SimpleNamespace(rule_type="cidr", pattern="203.0.113.0/24")

    assert _matching_ips_for_rule(rule, ["203.0.113.10", "198.51.100.10", "bad-ip"]) == ["203.0.113.10"]


def test_intent_and_page_scores_are_capped():
    assert _lead_score(request_count=2, core_page_hits=1, recent_hits=1) == 45
    assert _lead_score(request_count=100, core_page_hits=100, recent_hits=100) == 100
    assert _page_score(request_count=5, organization_count=2, core_page_hits=1) == 58
    assert _page_score(request_count=100, organization_count=100, core_page_hits=100) == 100
