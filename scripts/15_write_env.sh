#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Проверяем существование .env файла
if [[ -f services/.env ]]; then 
    echo "✅ services/.env уже существует"
    exit 0
fi

echo "🔧 Создание файла переменных окружения..."

# Запрашиваем основные настройки
read -p "Timezone [Europe/Moscow]: " TZ; TZ=${TZ:-Europe/Moscow}
read -s -p "IMMICH_DB_PASSWORD: " IMMICH_DB_PASSWORD; echo
read -p "PUID (id -u) [1000]: " PUID; PUID=${PUID:-1000}
read -p "PGID (id -g) [1000]: " PGID; PGID=${PGID:-1000}
read -p "Allow Vaultwarden signups now? (true/false) [false]: " VW; VW=${VW:-false}

# Запрашиваем настройки для агента
echo ""
echo "🤖 Настройки Homelab Agent:"
read -p "GIGACHAT_CREDENTIALS (обязательно): " GIGACHAT_CREDENTIALS
read -p "TAVILY_API_KEY (обязательно, для поиска в интернете): " TAVILY_API_KEY
read -p "GITHUB_TOKEN (опционально, для GitHub API): " GITHUB_TOKEN
read -p "GITHUB_WEBHOOK_SECRET (опционально, для безопасности webhook): " GITHUB_WEBHOOK_SECRET

# Проверяем обязательные поля
if [ -z "$GIGACHAT_CREDENTIALS" ]; then
    echo "❌ GIGACHAT_CREDENTIALS обязателен для работы агента"
    exit 1
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "❌ TAVILY_API_KEY обязателен для поиска в интернете"
    exit 1
fi

# Создаем .env файл для основных сервисов
cat > services/.env <<EOF
# Основные настройки
TZ=$TZ
IMMICH_DB_PASSWORD=$IMMICH_DB_PASSWORD
PUID=$PUID
PGID=$PGID
VW_SIGNUPS_ALLOWED=$VW
LAN_IP=${HOMELAB_HOST:-your_local_ip}

# Настройки для агента (будут скопированы в agent-web/.env)
GIGACHAT_CREDENTIALS=$GIGACHAT_CREDENTIALS
TAVILY_API_KEY=$TAVILY_API_KEY
GITHUB_TOKEN=$GITHUB_TOKEN
GITHUB_WEBHOOK_SECRET=$GITHUB_WEBHOOK_SECRET
EOF

# Создаем .env файл для агента
if [ ! -f agent-web/.env ]; then
    cat > agent-web/.env <<EOF
# Конфигурация Homelab Agent

# Временная зона
TZ=$TZ

# GigaChat API
GIGACHAT_CREDENTIALS=$GIGACHAT_CREDENTIALS

# Tavily Search API
TAVILY_API_KEY=$TAVILY_API_KEY

# GitHub API
GITHUB_TOKEN=${GITHUB_TOKEN:-}
GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET:-}

# База данных агента
AGENT_DB_PASSWORD=CHANGE_ME_strong_password

# Настройки GitHub polling
POLLING_INTERVAL=300

# Настройки сервера
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Логирование
LOG_LEVEL=INFO
LOG_FILE=/app/logs/homelab-agent.log
EOF
    echo "✅ agent-web/.env создан"
fi

echo "✅ services/.env создан"
echo ""
echo "📋 Следующие шаги:"
echo "1. Запустите основные сервисы: ./scripts/20_deploy_core.sh"
echo "2. Разверните агента: ./scripts/40_deploy_agent_web.sh"
echo "3. Настройте прокси (опционально): ./scripts/30_deploy_proxy_*.sh"
echo "4. Настройте UFW: ./scripts/50_configure_ufw.sh"
