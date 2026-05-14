import argparse
import json
import logging
from pathlib import Path

import requests

from config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_offset(offset_path: Path) -> int:
    if not offset_path.exists():
        return 0
    try:
        return int(json.loads(offset_path.read_text(encoding="utf-8")).get("offset", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("Invalid offset file, start from 0: %s", offset_path)
        return 0


def save_offset(offset_path: Path, offset: int) -> None:
    offset_path.write_text(json.dumps({"offset": offset}, ensure_ascii=False), encoding="utf-8")


def post_log(api_base_url: str, site_id: int, raw_log: str) -> None:
    url = f"{api_base_url.rstrip('/')}/api/collect/access-log"
    response = requests.post(url, json={"site_id": site_id, "raw_log": raw_log}, timeout=5)
    response.raise_for_status()


def collect_once(log_path: Path, offset_path: Path, api_base_url: str, site_id: int) -> None:
    offset = load_offset(offset_path)
    if not log_path.exists():
        raise FileNotFoundError(f"log file not found: {log_path}")

    current_size = log_path.stat().st_size
    if offset > current_size:
        logger.info("Log file appears rotated/truncated, reset offset from %s to 0", offset)
        offset = 0

    with log_path.open("r", encoding="utf-8", errors="replace") as fp:
        fp.seek(offset)
        while True:
            line = fp.readline()
            if not line:
                break
            raw_log = line.strip()
            if not raw_log:
                offset = fp.tell()
                save_offset(offset_path, offset)
                continue
            try:
                post_log(api_base_url, site_id, raw_log)
                logger.info("Reported log at offset=%s", fp.tell())
            except requests.RequestException as exc:
                logger.error("Report failed at offset=%s: %s", fp.tell(), exc)
            offset = fp.tell()
            save_offset(offset_path, offset)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Nginx access.log collector")
    parser.add_argument("--log-path", default=settings.log_path)
    parser.add_argument("--offset-path", default=settings.offset_path)
    parser.add_argument("--api-base-url", default=settings.api_base_url)
    parser.add_argument("--site-id", type=int, default=settings.site_id)
    args = parser.parse_args()

    collect_once(
        log_path=Path(args.log_path),
        offset_path=Path(args.offset_path),
        api_base_url=args.api_base_url,
        site_id=args.site_id,
    )


if __name__ == "__main__":
    main()
