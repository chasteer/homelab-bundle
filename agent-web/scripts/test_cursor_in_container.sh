#!/bin/bash
# Диагностика Cursor CLI внутри homelab-agent
# Запуск: bash scripts/test_cursor_in_container.sh
set -eu

cd "$(dirname "$0")/.." || exit 1

echo "=== env ==="
docker compose exec agent sh -c '
  if [ -n "$CURSOR_API_KEY" ]; then echo "CURSOR_API_KEY=set"; else echo "CURSOR_API_KEY=MISSING"; fi
  echo "WORKSPACE=$CURSOR_WORKSPACE"
  ls -la "$CURSOR_WORKSPACE" 2>/dev/null | head -5
'

echo ""
echo "=== quick agent (json) ==="
docker compose exec agent /home/agent/.local/bin/agent \
  -p --trust --approve-mcps --sandbox disabled \
  --mode plan --output-format json \
  --workspace /app/homelab \
  "Ответь одним словом: OK"

echo ""
echo "=== API test endpoint ==="
HOST="127.0.0.1"
if [ -f .env ]; then
  HOST=$(grep -E '^HOMELAB_HOST=' .env | head -1 | cut -d= -f2- | tr -d '\r"' || true)
fi
HOST=${HOST:-127.0.0.1}
echo "URL: http://${HOST}:8000/api/webhook/uptime-kuma/test-cursor"
curl -s -X POST "http://${HOST}:8000/api/webhook/uptime-kuma/test-cursor" | python3 -m json.tool
