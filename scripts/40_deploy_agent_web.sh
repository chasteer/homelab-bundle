#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Развертывание Homelab Agent..."

cd "$(dirname "$0")/../agent-web"

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "📝 Файл .env не найден, создаем на основе services/.env..."
    
    # Проверяем наличие services/.env
    if [ ! -f "../services/.env" ]; then
        echo "❌ Файл ../services/.env не найден"
        echo "Запустите сначала: ./scripts/15_write_env.sh"
        exit 1
    fi
    
    # Копируем переменные из services/.env
    source ../services/.env
    
    # Создаем .env для агента
    cat > .env <<EOF
# Homelab Incident Service — см. agent-web/env.example

TZ=${TZ:-Europe/Moscow}
HOMELAB_HOST=${HOMELAB_HOST:-your_local_ip}

CURSOR_API_KEY=
CURSOR_WORKSPACE=/app/homelab
CURSOR_AGENT_MODE=ask
CURSOR_TELEGRAM_MAX_CHARS=1400
CURSOR_OUTPUT_FORMAT=json

VPS_WEBHOOK_URL=https://your_vps_domain.com/api/uptime-alerts
UPTIME_KUMA_URL=http://uptime-kuma:3001
UPTIME_KUMA_API=
AGENT_WEBHOOK_URL=http://${HOMELAB_HOST:-your_local_ip}:8000/api/webhook/uptime-kuma

GITHUB_TOKEN=${GITHUB_TOKEN:-}
GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET:-}
AGENT_DB_PASSWORD=CHANGE_ME_strong_password
POLLING_INTERVAL=300
EOF
    
    echo "✅ .env файл создан на основе services/.env"
fi

# Проверяем переменные окружения
source .env

if [ -z "${CURSOR_API_KEY:-}" ]; then
    echo "⚠️  CURSOR_API_KEY не задан — анализ инцидентов не будет работать"
    echo "    Получите ключ: https://cursor.com/dashboard"
fi

if [ -z "${VPS_WEBHOOK_URL:-}" ] || [ "${VPS_WEBHOOK_URL}" = "https://your_vps_domain.com/api/uptime-alerts" ]; then
    echo "⚠️  Задайте VPS_WEBHOOK_URL в .env для Telegram"
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "⚠️  GITHUB_TOKEN не задан (опционально, для polling)"
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p data/index logs github-config

# Проверяем, что сеть homelab существует
if sudo docker network ls | grep -q " homelab "; then
    echo "✅ Сеть homelab найдена"
else
    echo "❌ Сеть homelab не найдена. Запустите сначала: ./scripts/20_deploy_core.sh"
    exit 1
fi

# Собираем и запускаем агента
echo "🐳 Сборка и запуск агента..."
sudo docker compose up -d --build

# Ждем запуска
echo "⏳ Ожидание запуска агента..."
sleep 15

# Проверяем статус
if sudo docker compose ps | grep -q "Up"; then
    echo "✅ Homelab Agent успешно запущен!"
    echo "🌐 API: http://${HOMELAB_HOST:-your_local_ip}:8000/api/health"
    echo "📊 Статус: $(sudo docker compose ps)"
    
    # Проверяем здоровье
    echo "🔍 Проверка здоровья сервиса..."
    if curl -f http://${HOMELAB_HOST:-your_local_ip}:8000/api/health >/dev/null 2>&1; then
        echo "✅ Сервис отвечает"
    else
        echo "⚠️  Сервис не отвечает, проверьте логи: sudo docker compose logs agent"
    fi
else
    echo "❌ Ошибка запуска агента"
    echo "📋 Логи:"
    sudo docker compose logs
    exit 1
fi

echo ""
echo "🎉 Homelab Agent развернут!"
echo ""
echo "📋 Полезные команды:"
echo "   sudo docker compose ps                    # Статус сервисов"
echo "   sudo docker compose logs -f agent        # Логи агента"
echo "   sudo docker compose logs -f github-polling # Логи GitHub polling"
echo "   sudo docker compose restart agent         # Перезапуск агента"
echo "   sudo docker compose down                  # Остановка всех сервисов"
echo ""
echo "🔧 Для запуска GitHub polling:"
echo "   sudo docker compose --profile polling up -d github-polling"
echo ""
echo "📚 Документация: agent-web/README.md, agent-web/INCIDENT_FLOW.md"
