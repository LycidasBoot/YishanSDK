from urllib.parse import urlsplit


def normalize_path(value: str | None) -> str:
    if not value:
        return "/"

    parsed = urlsplit(value)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    return path
