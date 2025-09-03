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
# Конфигурация Homelab Agent

# Временная зона
TZ=${TZ:-Europe/Moscow}

# GigaChat API
GIGACHAT_CREDENTIALS=${GIGACHAT_CREDENTIALS:-}

# Tavily Search API
TAVILY_API_KEY=${TAVILY_API_KEY:-}

# GitHub API
GITHUB_TOKEN=${GITHUB_TOKEN:-}
GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET:-}

# База данных агента
AGENT_DB_PASSWORD=agent123

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
    
    echo "✅ .env файл создан на основе services/.env"
fi

# Проверяем переменные окружения
source .env

if [ -z "${GIGACHAT_CREDENTIALS:-}" ]; then
    echo "❌ GIGACHAT_CREDENTIALS не задан в .env"
    exit 1
fi

if [ -z "${TAVILY_API_KEY:-}" ]; then
    echo "❌ TAVILY_API_KEY не задан в .env"
    exit 1
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo "⚠️  GITHUB_TOKEN не задан. GitHub интеграция будет недоступна"
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
    echo "🌐 Веб-интерфейс: http://${HOMELAB_HOST:-your_local_ip}:8000"
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
echo "📚 Документация: README.md"
