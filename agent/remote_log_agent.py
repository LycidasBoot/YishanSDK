import argparse
import json
import logging
from pathlib import Path

import paramiko
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
    offset_path.parent.mkdir(parents=True, exist_ok=True)
    offset_path.write_text(json.dumps({"offset": offset}, ensure_ascii=False), encoding="utf-8")


def post_log(api_base_url: str, site_id: int, raw_log: str) -> None:
    url = f"{api_base_url.rstrip('/')}/api/collect/access-log"
    response = requests.post(url, json={"site_id": site_id, "raw_log": raw_log}, timeout=10)
    response.raise_for_status()


def connect_ssh(
    host: str,
    port: int,
    username: str,
    password: str | None = None,
    key_path: str | None = None,
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        key_filename=key_path,
        look_for_keys=False,
        timeout=15,
        banner_timeout=15,
        auth_timeout=15,
    )
    return client


def collect_remote_once(
    host: str,
    port: int,
    username: str,
    password: str | None,
    key_path: str | None,
    remote_log_path: str,
    offset_path: Path,
    api_base_url: str,
    site_id: int,
) -> None:
    offset = load_offset(offset_path)
    client = connect_ssh(host, port, username, password, key_path)
    try:
        with client.open_sftp() as sftp:
            stat = sftp.stat(remote_log_path)
            if offset > stat.st_size:
                logger.info("Remote log appears rotated/truncated, reset offset from %s to 0", offset)
                offset = 0

            with sftp.open(remote_log_path, "r") as fp:
                fp.seek(offset)
                while True:
                    line = fp.readline()
                    if not line:
                        break
                    if isinstance(line, bytes):
                        raw_log = line.decode("utf-8", errors="replace").strip()
                    else:
                        raw_log = line.strip()
                    next_offset = fp.tell()
                    if raw_log:
                        try:
                            post_log(api_base_url, site_id, raw_log)
                            logger.info("Reported remote log at offset=%s", next_offset)
                        except requests.RequestException as exc:
                            logger.error("Report failed at offset=%s: %s", next_offset, exc)
                    offset = next_offset
                    save_offset(offset_path, offset)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull remote Nginx access.log over SSH/SFTP")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password")
    parser.add_argument("--key-path")
    parser.add_argument("--remote-log-path", required=True)
    parser.add_argument("--offset-path", required=True)
    parser.add_argument("--api-base-url", default=settings.api_base_url)
    parser.add_argument("--site-id", type=int, required=True)
    args = parser.parse_args()
    if not args.password and not args.key_path:
        parser.error("one of --password or --key-path is required")

    collect_remote_once(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        key_path=args.key_path,
        remote_log_path=args.remote_log_path,
        offset_path=Path(args.offset_path),
        api_base_url=args.api_base_url,
        site_id=args.site_id,
    )


if __name__ == "__main__":
    main()
