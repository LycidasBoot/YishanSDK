from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from ipaddress import ip_address

import requests

from config.settings import settings


@dataclass(frozen=True)
class IpLocation:
    location: str
    network_owner: str | None = None
    source: str = "local"


def _local_location(client_ip: str) -> IpLocation | None:
    try:
        ip = ip_address(client_ip)
    except ValueError:
        return IpLocation(location="无效 IP", source="local")

    if ip.is_loopback:
        return IpLocation(location="本机地址", source="local")
    if ip.is_private:
        return IpLocation(location="内网地址", source="local")
    if ip.is_link_local:
        return IpLocation(location="链路本地地址", source="local")
    if ip.is_multicast:
        return IpLocation(location="组播地址", source="local")
    if ip.is_reserved or ip.is_unspecified:
        return IpLocation(location="保留地址", source="local")

    return None


def _format_location(payload: dict) -> str:
    country = str(payload.get("country") or "").strip()
    region = str(payload.get("regionName") or "").strip()
    city = str(payload.get("city") or "").strip()
    parts = []
    if country:
        parts.append("中国" if country == "China" else country)
    for value in (region, city):
        if value and value not in parts:
            parts.append(value)
    return " · ".join(parts) if parts else "公网 IP"


def _fallback_public_location() -> IpLocation:
    return IpLocation(location="公网 IP · 待接入归属库", source="local")


def _lookup_ip_api_batch(public_ips: list[str]) -> dict[str, IpLocation]:
    if not public_ips:
        return {}

    url = "http://ip-api.com/batch"
    params = {
        "fields": "status,country,regionName,city,isp,org,as,query",
        "lang": "zh-CN",
    }
    response = requests.post(
        url,
        params=params,
        json=[{"query": ip} for ip in public_ips],
        timeout=settings.ip_location_timeout_seconds,
    )
    response.raise_for_status()

    locations: dict[str, IpLocation] = {}
    for item in response.json():
        query = str(item.get("query") or "")
        if not query or item.get("status") != "success":
            continue
        owner = str(item.get("org") or item.get("isp") or item.get("as") or "").strip() or None
        locations[query] = IpLocation(location=_format_location(item), network_owner=owner, source="ip-api")
    return locations


@lru_cache(maxsize=4096)
def lookup_ip_location(client_ip: str) -> IpLocation:
    local = _local_location(client_ip)
    if local:
        return local

    if settings.ip_location_provider.lower() != "ip-api":
        return _fallback_public_location()

    try:
        return _lookup_ip_api_batch([client_ip]).get(client_ip, _fallback_public_location())
    except requests.RequestException:
        return _fallback_public_location()


def lookup_ip_locations(client_ips: list[str]) -> dict[str, IpLocation]:
    results: dict[str, IpLocation] = {}
    public_ips: list[str] = []

    for client_ip in client_ips:
        local = _local_location(client_ip)
        if local:
            results[client_ip] = local
        elif settings.ip_location_provider.lower() == "ip-api":
            public_ips.append(client_ip)
        else:
            results[client_ip] = _fallback_public_location()

    if public_ips:
        try:
            results.update(_lookup_ip_api_batch(public_ips))
        except requests.RequestException:
            pass
        for client_ip in public_ips:
            results.setdefault(client_ip, _fallback_public_location())

    return results
