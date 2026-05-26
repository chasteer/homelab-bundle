#!/usr/bin/env bash
# Проверка VPS webhook из контейнера homelab-agent (та же сеть, что и в проде).
set -euo pipefail
cd "$(dirname "$0")/.."

HOST="${HOMELAB_HOST:-127.0.0.1}"

echo "=== 1) test-vps через API агента ==="
curl -sS -X POST "http://${HOST}:8000/api/webhook/uptime-kuma/test-vps" | python3 -m json.tool

echo ""
echo "=== 2) прямой curl к VPS_WEBHOOK_URL из контейнера ==="
docker compose exec -T agent python3 - <<'PY'
import json
import os
import requests

url = os.environ.get("VPS_WEBHOOK_URL", "").strip().rstrip("/")
if not url:
    raise SystemExit("VPS_WEBHOOK_URL не задан в контейнере")

payload = {
    "source": "homelab_uptime_kuma",
    "service": "curl-test",
    "status": "up",
    "host": os.environ.get("HOMELAB_HOST", "test"),
    "incident_analysis": "curl test from container",
}
print("POST", url)
r = requests.post(
    url, json=payload, timeout=(15, 90), allow_redirects=False,
    proxies={"http": None, "https": None},
)
print("status:", r.status_code)
print(r.text[:500])
PY
