#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../services"

echo "🔧 Проверка и настройка сети homelab..."

# Проверяем, что основная сеть homelab существует
if sudo docker network ls | grep -q " homelab "; then
    echo "✅ Сеть homelab уже существует"
else
    echo "🌐 Создаем сеть homelab..."
    sudo docker network create homelab
    echo "✅ Сеть homelab создана"
fi

echo "🚀 Запуск основных сервисов..."
# Запускаем сервисы
sudo docker compose --env-file .env -f docker-compose.yml up -d

echo "✅ Core services deployed."
