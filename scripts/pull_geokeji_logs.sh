#!/usr/bin/env bash
set -euo pipefail

cd "${CRAWLER_STATS_APP_DIR:-/root/apps/crawler_stats_sdk}"

.venv/bin/python -m agent.remote_log_agent \
  --host "${GEOKEJI_LOG_HOST:-8.141.29.188}" \
  --username "${GEOKEJI_LOG_USERNAME:-crawlerlog}" \
  --key-path "${GEOKEJI_LOG_KEY_PATH:-/root/apps/crawler_stats_sdk/runtime/geokeji_pull_ed25519}" \
  --remote-log-path "${GEOKEJI_LOG_PATH:-/var/log/nginx/geokeji.access.log}" \
  --offset-path "${GEOKEJI_OFFSET_PATH:-/root/apps/crawler_stats_sdk/runtime/geokeji.offset.json}" \
  --api-base-url "${GEOKEJI_API_BASE_URL:-http://127.0.0.1:9876}" \
  --site-id "${GEOKEJI_SITE_ID:-1}"
