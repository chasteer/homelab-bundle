#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Очистка Docker ресурсов..."

# Останавливаем все контейнеры
echo "🛑 Остановка всех контейнеров..."
sudo docker compose -f services/docker-compose.yml down 2>/dev/null || echo "⚠️  Сервисы уже остановлены"
sudo docker compose -f agent-web/docker-compose.yml down 2>/dev/null || echo "⚠️  Агент уже остановлен"

# Удаляем все контейнеры homelab
echo "🗑️  Удаление контейнеров homelab..."
sudo docker ps -a --filter "name=homelab" --filter "name=jellyfin" --filter "name=immich" --filter "name=vaultwarden" --filter "name=uptime-kuma" --filter "name=torrserver" --filter "name=agent" -q | xargs -r sudo docker rm -f

# Удаляем все образы homelab
echo "🗑️  Удаление образов homelab..."
sudo docker images --filter "reference=homelab*" -q | xargs -r sudo docker rmi -f

# Удаляем все сети homelab (кроме основной)
echo "🌐 Очистка сетей homelab..."
for network in $(sudo docker network ls | grep "homelab" | awk '{print $2}'); do
    if [ "$network" != "homelab" ]; then
        echo "🗑️  Удаляем сеть: $network"
        sudo docker network rm "$network" 2>/dev/null || echo "⚠️  Не удалось удалить сеть $network"
    fi
done

# Удаляем все volumes homelab (опционально)
echo "💾 Очистка volumes (опционально)..."
read -p "Удалить все volumes homelab? Это удалит ВСЕ данные! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Удаление volumes..."
    sudo docker volume ls --filter "name=homelab" -q | xargs -r sudo docker volume rm -f
    sudo docker volume ls --filter "name=agent" -q | xargs -r sudo docker volume rm -f
    echo "✅ Volumes удалены"
else
    echo "⚠️  Volumes сохранены"
fi

echo "✅ Очистка завершена!"
echo ""
echo "🔧 Теперь можно запустить заново:"
echo "   ./scripts/deploy_all.sh"
