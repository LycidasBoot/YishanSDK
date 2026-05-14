import re
from datetime import datetime
from zoneinfo import ZoneInfo


class NginxLogParseError(ValueError):
    pass


COMBINED_LOG_RE = re.compile(
    r'(?P<client_ip>\S+) \S+ \S+ '
    r'\[(?P<request_time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes_sent>\S+) '
    r'"(?P<referer>[^"]*)" '
    r'"(?P<user_agent>[^"]*)"'
)

GEO_AI_LOG_RE = re.compile(
    r'(?P<client_ip>[^|]+?)\s*\|\s*'
    r'\[(?P<request_time>[^\]]+)\]\s*\|\s*'
    r'"(?P<host>[^"]*)"\s*\|\s*'
    r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)"\s*\|\s*'
    r'(?P<status>\d{3})\s*\|\s*'
    r'(?P<bytes_sent>\S+)\s*\|\s*'
    r'"(?P<referer>[^"]*)"\s*\|\s*'
    r'"(?P<user_agent>[^"]*)"'
)


def _parse_request_time(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%d/%b/%Y:%H:%M:%S %z").astimezone(ZoneInfo("UTC"))
    except ValueError as exc:
        raise NginxLogParseError("Invalid request time") from exc


def _parse_bytes_sent(value: str) -> int:
    return 0 if value == "-" else int(value)


def _empty_to_none(value: str) -> str | None:
    return None if value == "-" else value


def parse_combined_log(raw_log: str) -> dict:
    match = COMBINED_LOG_RE.match(raw_log.strip())
    if not match:
        raise NginxLogParseError("Unsupported Nginx access log format")

    data = match.groupdict()
    return {
        "client_ip": data["client_ip"],
        "request_time": _parse_request_time(data["request_time"]),
        "method": data["method"],
        "path": data["path"],
        "protocol": data["protocol"],
        "status": int(data["status"]),
        "bytes_sent": _parse_bytes_sent(data["bytes_sent"]),
        "referer": _empty_to_none(data["referer"]),
        "user_agent": _empty_to_none(data["user_agent"]),
    }


def parse_geo_ai_log(raw_log: str) -> dict:
    match = GEO_AI_LOG_RE.match(raw_log.strip())
    if not match:
        raise NginxLogParseError("Unsupported geo_ai Nginx access log format")

    data = match.groupdict()
    return {
        "client_ip": data["client_ip"].strip(),
        "request_time": _parse_request_time(data["request_time"]),
        "method": data["method"],
        "path": data["path"],
        "protocol": data["protocol"],
        "status": int(data["status"]),
        "bytes_sent": _parse_bytes_sent(data["bytes_sent"]),
        "referer": _empty_to_none(data["referer"]),
        "user_agent": _empty_to_none(data["user_agent"]),
    }


def parse_access_log(raw_log: str) -> dict:
    parsers = (parse_combined_log, parse_geo_ai_log)
    for parser in parsers:
        try:
            return parser(raw_log)
        except NginxLogParseError:
            continue
    raise NginxLogParseError("Unsupported Nginx access log format")
