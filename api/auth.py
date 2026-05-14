import base64
import hashlib
import hmac
import time

from fastapi import Request

from config.settings import settings

SESSION_COOKIE = "crawler_stats_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12


def _session_secret() -> str:
    return settings.session_secret or settings.dashboard_password


def verify_credentials(username: str, password: str) -> bool:
    return hmac.compare_digest(username, settings.dashboard_username) and hmac.compare_digest(
        password,
        settings.dashboard_password,
    )


def create_session_token(username: str) -> str:
    issued_at = str(int(time.time()))
    payload = f"{username}:{issued_at}"
    signature = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        username, issued_at, signature = decoded.rsplit(":", 2)
        payload = f"{username}:{issued_at}"
    except (ValueError, UnicodeDecodeError):
        return False

    expected = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False
    if not hmac.compare_digest(username, settings.dashboard_username):
        return False
    try:
        issued_at_int = int(issued_at)
    except ValueError:
        return False
    return int(time.time()) - issued_at_int <= SESSION_MAX_AGE_SECONDS


def is_authenticated(request: Request) -> bool:
    return verify_session_token(request.cookies.get(SESSION_COOKIE))
