#!/usr/bin/env bash
# Проверка Cursor CLI внутри контейнера homelab-agent
set -euo pipefail

AGENT_URL="${AGENT_URL:-http://localhost:8000}"

echo "=== Health ==="
curl -sf "${AGENT_URL}/api/health" | python3 -m json.tool

echo ""
echo "=== Agent binary in container ==="
docker compose exec agent /home/agent/.local/bin/agent --version

echo ""
echo "=== Test incident analysis ==="
curl -sf -X POST "${AGENT_URL}/api/webhook/uptime-kuma/test-cursor" | python3 -m json.tool
