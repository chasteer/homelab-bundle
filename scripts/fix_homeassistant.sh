#!/usr/bin/env bash
# Home Assistant за Caddy: trusted_proxies + external_url
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CFG="/srv/homeassistant/configuration.yaml"
MARKER="# homelab-reverse-proxy"

if [[ ! -d /srv/homeassistant ]]; then
  echo "❌ Нет /srv/homeassistant — запустите ./scripts/10_prepare_dirs.sh"
  exit 1
fi

PATCH_BLOCK='
# homelab-reverse-proxy
homeassistant:
  external_url: "https://homeassistant.home.arpa"
  internal_url: "http://homeassistant:8123"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12
    - 192.168.0.0/16
    - 10.0.0.0/8
'

patch_via_docker() {
  docker ps --format '{{.Names}}' | grep -qx homeassistant || return 1
  docker exec homeassistant grep -q "$MARKER" /config/configuration.yaml 2>/dev/null && return 0
  printf '%s' "$PATCH_BLOCK" | docker exec -i homeassistant sh -c 'cat >>/config/configuration.yaml'
  return 0
}

patch_config() {
  if grep -q "$MARKER" "$CFG" 2>/dev/null; then
    echo "ℹ️  configuration.yaml уже содержит настройки reverse proxy"
    return 0
  fi
  printf '%s' "$PATCH_BLOCK" >>"$CFG"
  echo "✅ Добавлены http / homeassistant URL в configuration.yaml"
}

if grep -q "$MARKER" "$CFG" 2>/dev/null; then
  echo "ℹ️  configuration.yaml уже содержит настройки reverse proxy"
elif [[ -w "$CFG" ]]; then
  patch_config
elif patch_via_docker; then
  echo "✅ Настройки добавлены через docker exec"
elif [[ $EUID -eq 0 ]]; then
  patch_config
  [[ -n "${SUDO_USER:-}" ]] && chown -R "${SUDO_USER}:${SUDO_USER}" /srv/homeassistant 2>/dev/null || true
else
  echo "Нужны права на $CFG. Запустите: sudo $0"
  exit 1
fi

echo "Перезапуск homeassistant..."
cd "$ROOT/services"
# shellcheck source=/dev/null
[[ -f .env ]] && source .env
docker compose restart homeassistant
sleep 8

echo "Проверка:"
docker compose ps homeassistant
if curl -sk --resolve homeassistant.home.arpa:443:"${HOMELAB_HOST:-127.0.0.1}" -o /dev/null -w "%{http_code}" https://homeassistant.home.arpa/ | grep -qE '200|302'; then
  echo "✅ https://homeassistant.home.arpa отвечает"
else
  echo "⚠️  Откройте https://homeassistant.home.arpa или http://${HOMELAB_HOST:-LAN_IP}:8123"
fi
