#!/usr/bin/env bash
# Создание services/.env и заготовки agent-web/.env (без устаревших GigaChat/Tavily).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

detect_lan_ip() {
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' \
    || hostname -I 2>/dev/null | awk '{print $1}' \
    || echo "192.168.1.200"
}

if [[ -f services/.env ]]; then
  echo "✅ services/.env уже существует"
else
  DEFAULT_IP="$(detect_lan_ip)"
  echo "🔧 Создание services/.env"
  read -p "Timezone [Europe/Moscow]: " TZ_IN
  TZ_IN="${TZ_IN:-Europe/Moscow}"
  read -p "LAN IP сервера (HOMELAB_HOST) [$DEFAULT_IP]: " HOST_IN
  HOST_IN="${HOST_IN:-$DEFAULT_IP}"
  read -s -p "Пароль БД Immich: " IMMICH_PW
  echo
  if [[ -z "$IMMICH_PW" ]]; then
    IMMICH_PW="$(openssl rand -base64 18 | tr -d '/+=' | head -c 20)"
    echo "  (сгенерирован случайный пароль Immich)"
  fi
  read -p "Разрешить регистрацию Vaultwarden? (true/false) [false]: " VW_SIGN
  VW_SIGN="${VW_SIGN:-false}"

  cat >services/.env <<EOF
# Создано scripts/write_env.sh
TZ=$TZ_IN
HOMELAB_HOST=$HOST_IN
IMMICH_DB_PASSWORD=$IMMICH_PW
PUID=$(id -u)
PGID=$(id -g)
VW_SIGNUPS_ALLOWED=$VW_SIGN
VW_DOMAIN=https://vaultwarden.home.arpa
EOF
  chmod 600 services/.env
  echo "✅ services/.env"
fi

# shellcheck source=/dev/null
source services/.env

if [[ ! -f agent-web/.env ]]; then
  AGENT_DB_PW="$(openssl rand -base64 18 | tr -d '/+=' | head -c 24)"
  cat >agent-web/.env <<EOF
# Создано scripts/write_env.sh — дополните CURSOR_API_KEY и VPS_WEBHOOK_URL
TZ=${TZ:-Europe/Moscow}
HOMELAB_HOST=${HOMELAB_HOST}

CURSOR_API_KEY=
CURSOR_WORKSPACE=/app/homelab
CURSOR_AGENT_MODE=ask
CURSOR_TELEGRAM_MAX_CHARS=1400
CURSOR_OUTPUT_FORMAT=json
CURSOR_CLI_TIMEOUT=300
CURSOR_INCIDENT_ENABLED=true
CURSOR_INCIDENT_REQUIRED=true

VPS_WEBHOOK_URL=https://your-vps.example.com/uptime-alerts
UPTIME_KUMA_URL=http://uptime-kuma:3001
UPTIME_KUMA_API=
AGENT_WEBHOOK_URL=http://${HOMELAB_HOST}:8000/api/webhook/uptime-kuma

AGENT_DB_PASSWORD=$AGENT_DB_PW
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=
CONTAINER_LOG_TAIL=150
CONTAINER_LOG_MAX_CHARS=12000
EOF
  chmod 600 agent-web/.env
  echo "✅ agent-web/.env (заполните CURSOR_API_KEY и VPS_WEBHOOK_URL)"
else
  echo "✅ agent-web/.env уже существует"
fi
