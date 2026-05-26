#!/usr/bin/env bash
# Единая установка Homelab: проверки → каталоги → .env → Docker → Caddy → агент.
#
# Использование:
#   ./setup.sh              интерактивная установка
#   ./setup.sh --check      только проверки (без изменений)
#   ./setup.sh --yes        меньше вопросов (UFW пропускается)
#   ./setup.sh --install-docker   установить Docker (Ubuntu)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

CHECK_ONLY=false
ASSUME_YES=false
SKIP_BOOTSTRAP=true
INSTALL_DOCKER=false
SKIP_UFW=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check|--check-only|-c) CHECK_ONLY=true ;;
    --yes|-y) ASSUME_YES=true; SKIP_UFW=true ;;
    --install-docker) INSTALL_DOCKER=true; SKIP_BOOTSTRAP=false ;;
    --skip-ufw) SKIP_UFW=true ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "Неизвестный аргумент: $1 (см. --help)"; exit 1 ;;
  esac
  shift
done

# --- вывод ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️${NC}  $*"; }
fail()  { echo -e "${RED}❌${NC} $*"; }
title() { echo ""; echo "══ $* ══"; }

CRITICAL=0
WARNINGS=0

check_ok()   { info "$1"; }
check_warn() { warn "$1"; WARNINGS=$((WARNINGS + 1)); }
check_fail() { fail "$1"; CRITICAL=$((CRITICAL + 1)); }

docker_cmd() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  else
    sudo docker "$@"
  fi
}

compose_cmd() {
  local dir="$1"
  shift
  if docker info >/dev/null 2>&1; then
    docker compose -f "$dir/docker-compose.yml" "$@"
  else
    sudo docker compose -f "$dir/docker-compose.yml" "$@"
  fi
}

# ─────────────────────────────────────────────────────────────
title "Проверка окружения"

if [[ ! -f README.md || ! -f services/docker-compose.yml ]]; then
  check_fail "Запускайте из корня репозитория home_lab"
else
  check_ok "Корень репозитория: $ROOT"
fi

for f in services/docker-compose.yml agent-web/docker-compose.yml proxy/docker-compose.caddy.yml; do
  if [[ -f "$f" ]]; then
    check_ok "Файл $f"
  else
    check_fail "Нет $f"
  fi
done

if command -v docker >/dev/null 2>&1; then
  check_ok "Docker установлен: $(docker --version 2>/dev/null | head -1)"
else
  check_fail "Docker не установлен (запустите: ./setup.sh --install-docker)"
fi

if docker compose version >/dev/null 2>&1; then
  check_ok "Docker Compose plugin"
elif command -v docker-compose >/dev/null 2>&1; then
  check_warn "Используется legacy docker-compose"
else
  check_fail "Docker Compose не найден"
fi

if docker info >/dev/null 2>&1; then
  check_ok "Доступ к Docker API (без sudo)"
elif sudo docker info >/dev/null 2>&1; then
  check_warn "Docker только через sudo. Добавьте пользователя в группу docker и перелогиньтесь:"
  echo "         sudo usermod -aG docker $USER"
else
  check_fail "Docker daemon недоступен (запущен ли сервис? systemctl status docker)"
fi

if command -v openssl >/dev/null 2>&1; then
  check_ok "openssl"
else
  check_fail "Нужен openssl"
fi

if command -v curl >/dev/null 2>&1; then
  check_ok "curl"
else
  check_warn "curl не найден (проверки health будут ограничены)"
fi

# Диск
if command -v df >/dev/null 2>&1; then
  avail_g="$(df -BG /srv 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}' || df -BG . | awk 'NR==2 {gsub(/G/,"",$4); print $4}')"
  if [[ -n "${avail_g:-}" && "$avail_g" -lt 20 ]] 2>/dev/null; then
    check_warn "Мало места на диске (~${avail_g}G свободно на /srv или /)"
  else
    check_ok "Место на диске: OK"
  fi
fi

title "Конфигурация (.env)"

if [[ -f services/.env ]]; then
  check_ok "services/.env"
  # shellcheck disable=SC1091
  set -a; source services/.env; set +a
  if [[ -z "${HOMELAB_HOST:-}" || "${HOMELAB_HOST}" == *"your_local"* ]]; then
    check_fail "В services/.env задайте HOMELAB_HOST (LAN IP сервера)"
  else
    check_ok "HOMELAB_HOST=$HOMELAB_HOST"
  fi
  if [[ "${IMMICH_DB_PASSWORD:-}" == "change_me"* || -z "${IMMICH_DB_PASSWORD:-}" ]]; then
    check_warn "Смените IMMICH_DB_PASSWORD в services/.env"
  fi
else
  check_fail "Нет services/.env — будет создан при установке (./scripts/write_env.sh)"
fi

if [[ -f agent-web/.env ]]; then
  check_ok "agent-web/.env"
  set -a; source agent-web/.env 2>/dev/null || true; set +a
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    check_warn "CURSOR_API_KEY не задан — анализ инцидентов не заработает"
  else
    check_ok "CURSOR_API_KEY задан"
  fi
  if [[ -z "${VPS_WEBHOOK_URL:-}" || "${VPS_WEBHOOK_URL}" == *"your-vps"* || "${VPS_WEBHOOK_URL}" == *"your_vps"* ]]; then
    check_warn "Задайте VPS_WEBHOOK_URL в agent-web/.env (Telegram)"
  else
    check_ok "VPS_WEBHOOK_URL задан"
  fi
else
  check_fail "Нет agent-web/.env — будет создан при установке"
fi

title "Прокси (Caddy)"

if [[ -f proxy/Caddyfile.template ]]; then
  check_ok "Caddyfile.template"
else
  check_warn "Нет proxy/Caddyfile.template"
fi

title "Docker (текущее состояние)"

if docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1; then
  if docker_cmd network ls 2>/dev/null | grep -q ' homelab '; then
    check_ok "Сеть Docker: homelab"
  else
    check_warn "Сеть homelab ещё не создана (создастся при deploy)"
  fi

  running="$(docker_cmd ps --format '{{.Names}}' 2>/dev/null | wc -l)"
  if [[ "$running" -gt 0 ]]; then
    check_ok "Запущено контейнеров: $running"
    docker_cmd ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null | head -20 || true
  else
    check_warn "Нет запущенных контейнеров homelab"
  fi
fi

title "DNS / hosts (на клиентах)"

if [[ -f services/.env ]]; then
  set -a; source services/.env; set +a
  echo "  Пропишите на ПК/роутере *.home.arpa → ${HOMELAB_HOST:-?}"
  echo "  Шаблон OpenWrt: dns/openwrt_home_arpa.conf"
  echo "  Linux hosts:    HOMELAB_HOST=${HOMELAB_HOST:-?} ./dns/set_local_hosts.sh"
fi

echo ""
echo "────────────────────────────────────────"
if [[ $CRITICAL -gt 0 ]]; then
  fail "Критичных проблем: $CRITICAL"
  if [[ $WARNINGS -gt 0 ]]; then warn "Предупреждений: $WARNINGS"; fi
  if $CHECK_ONLY; then exit 1; fi
  echo ""
  echo "Исправьте критичные пункты или запустите установку — часть будет исправлена автоматически."
  if ! $ASSUME_YES; then
    read -p "Продолжить установку несмотря на ошибки? (y/N): " cont
    [[ "${cont,,}" == "y" ]] || exit 1
  fi
else
  info "Критичных проблем нет"
  [[ $WARNINGS -gt 0 ]] && warn "Предупреждений: $WARNINGS"
  if $CHECK_ONLY; then
    echo ""
    info "Режим --check: изменений не вносилось"
    exit 0
  fi
fi

$CHECK_ONLY && exit 0

# ═══════════════════════════════════════════════════════════
# УСТАНОВКА
# ═══════════════════════════════════════════════════════════
echo ""
echo "🚀 Установка Homelab"
echo "=================================="

if $INSTALL_DOCKER || { ! command -v docker >/dev/null 2>&1 && ! $SKIP_BOOTSTRAP; }; then
  title "Установка Docker"
  if [[ -f /etc/os-release ]] && grep -qi ubuntu /etc/os-release; then
    ./scripts/00_bootstrap_ubuntu.sh
    warn "Если Docker без sudo не работает — выйдите из сессии и войдите снова (группа docker)"
  else
    fail "Автоустановка Docker только для Ubuntu. Установите Docker вручную."
    exit 1
  fi
fi

title "Каталоги /srv"
./scripts/10_prepare_dirs.sh

title "Файлы .env"
if [[ ! -f services/.env ]] || [[ ! -f agent-web/.env ]]; then
  ./scripts/write_env.sh
else
  info "services/.env и agent-web/.env на месте"
fi

set -a
# shellcheck source=/dev/null
source services/.env
set +a

title "Сеть Docker homelab"
if ! docker_cmd network ls | grep -q ' homelab '; then
  docker_cmd network create homelab
  info "Сеть homelab создана"
else
  info "Сеть homelab уже есть"
fi

title "Основные сервисы (services/)"
compose_cmd services --env-file services/.env up -d
info "Ожидание старта (15 с)…"
sleep 15
compose_cmd services ps

title "Caddy (HTTPS)"
./scripts/30_deploy_proxy_caddy.sh

title "Homelab Agent (incident service)"
cd agent-web
if docker info >/dev/null 2>&1; then
  docker compose --env-file .env up -d --build
else
  sudo docker compose --env-file .env up -d --build
fi
cd "$ROOT"
sleep 10

if ! $SKIP_UFW; then
  title "UFW (опционально)"
  if $ASSUME_YES; then
    warn "UFW пропущен (--yes)"
  else
    read -p "Настроить UFW? (y/N): " ufw_ans
    if [[ "${ufw_ans,,}" == "y" ]]; then
      ./scripts/50_configure_ufw.sh
    fi
  fi
fi

title "Home Assistant (reverse proxy)"
if docker ps --format '{{.Names}}' | grep -qx homeassistant; then
  if ! grep -q homelab-reverse-proxy /srv/homeassistant/configuration.yaml 2>/dev/null; then
    if docker exec homeassistant test -w /config/configuration.yaml 2>/dev/null; then
      "$ROOT/scripts/fix_homeassistant.sh" || warn "HA: запустите ./scripts/fix_homeassistant.sh"
    else
      warn "HA: sudo ./scripts/fix_homeassistant.sh (configuration.yaml)"
    fi
  else
    info "Home Assistant: reverse proxy уже настроен"
  fi
fi

title "Проверка"
./scripts/check_status.sh || true

# shellcheck source=/dev/null
source services/.env
HOST="${HOMELAB_HOST:-127.0.0.1}"

echo ""
echo "🎉 Установка завершена"
echo ""
echo "📋 HTTPS (после DNS/hosts и импорта CA Caddy):"
echo "   https://jellyfin.home.arpa"
echo "   https://vaultwarden.home.arpa"
echo "   https://kuma.home.arpa"
echo "   https://dozzle.home.arpa        — логи Docker"
echo "   https://it-tools.home.arpa"
echo "   https://homeassistant.home.arpa"
echo ""
echo "📋 Прямые порты:"
echo "   http://${HOST}:8096  Jellyfin"
echo "   http://${HOST}:8081  Vaultwarden (моб. клиенты)"
echo "   http://${HOST}:8000  Agent API"
echo ""
echo "🔐 Импорт CA (зелёный замок в LAN): ./scripts/export_caddy_root_ca.sh"
echo "🔍 Повторная проверка:              ./setup.sh --check"
echo "📚 Документация:                    docs/HOMELAB_STACK.md"
