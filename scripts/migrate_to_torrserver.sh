#!/usr/bin/env bash
set -euo pipefail

# Скрипт миграции с qBittorrent на TorrServer

echo "🚀 Миграция с qBittorrent на TorrServer..."
echo "=========================================="

# Проверяем, что мы в корневой директории
if [ ! -f "services/docker-compose.yml" ]; then
    echo "❌ Запустите скрипт из корневой директории проекта"
    exit 1
fi

# Функция для проверки успешности выполнения
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

echo "🔍 Проверка текущего состояния..."

# Проверяем, запущен ли qBittorrent
if docker ps | grep -q "qbittorrent"; then
    echo "⚠️  qBittorrent запущен. Останавливаем..."
    cd services
    docker compose stop qbittorrent
    cd ..
    check_success "qBittorrent остановлен"
else
    echo "ℹ️  qBittorrent не запущен"
fi

# Создаем резервную копию конфигурации qBittorrent
echo "💾 Создание резервной копии qBittorrent..."
if [ -d "/srv/media/config/qb" ]; then
    backup_dir="backups/qbittorrent_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    cp -r /srv/media/config/qb "$backup_dir/"
    echo "✅ Резервная копия создана: $backup_dir"
else
    echo "ℹ️  Конфигурация qBittorrent не найдена"
fi

# Создаем директории для TorrServer
echo "📁 Создание директорий для TorrServer..."
sudo mkdir -p /srv/media/config/torrserver
sudo mkdir -p /srv/media/cache
sudo chown -R $USER:$USER /srv/media/config/torrserver /srv/media/cache
check_success "Директории TorrServer созданы"

# Останавливаем все сервисы
echo "🛑 Остановка всех сервисов..."
cd services
docker compose down
cd ..
check_success "Сервисы остановлены"

# Обновляем docker-compose.yml
echo "📝 Обновление docker-compose.yml..."
if [ -f "services/docker-compose.yml" ]; then
    # Создаем резервную копию
    cp services/docker-compose.yml "services/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Заменяем qBittorrent на TorrServer
    sed -i 's/qbittorrent:/torrserver:/g' services/docker-compose.yml
    sed -i 's/qbittorrent/torrserver/g' services/docker-compose.yml
    sed -i 's/ghcr\.io\/linuxserver\/qbittorrent:latest/ghcr.io\/yourok\/torrserver:latest/g' services/docker-compose.yml
    sed -i 's/8080:8080/8090:8090/g' services/docker-compose.yml
    sed -i 's/6881:6881/# 6881:6881/g' services/docker-compose.yml
    sed -i 's/6881:6881\/udp/# 6881:6881\/udp/g' services/docker-compose.yml
    
    # Обновляем переменные окружения
    sed -i '/PUID:/d' services/docker-compose.yml
    sed -i '/PGID:/d' services/docker-compose.yml
    sed -i '/WEBUI_PORT:/d' services/docker-compose.yml
    sed -i '/UMASK:/d' services/docker-compose.yml
    
    # Добавляем переменные TorrServer
    sed -i '/environment:/a\      - TS_PORT=8090\n      - TS_DONTKILL=1\n      - TS_HTTPAUTH=0\n      - TS_CONF_PATH=/opt/ts/config\n      - TS_TORR_DIR=/opt/ts/torrents\n      - TS_LOG_PATH=/opt/ts/log' services/docker-compose.yml
    
    # Обновляем volumes
    sed -i 's|/srv/media/config/qb:/config|/srv/media/config/torrserver:/opt/ts/config|g' services/docker-compose.yml
    sed -i 's|/srv/media/downloads:/downloads|/srv/media/downloads:/opt/ts/torrents|g' services/docker-compose.yml
    sed -i '/volumes:/a\      - /srv/media/cache:/opt/ts/cache' services/docker-compose.yml
    
    # Обновляем healthcheck
    sed -i 's|http://localhost:8080|http://localhost:8090|g' services/docker-compose.yml
    
    echo "✅ docker-compose.yml обновлен"
else
    echo "❌ services/docker-compose.yml не найден"
    exit 1
fi

# Обновляем UFW правила
echo "🔒 Обновление UFW правил..."
if command -v ufw >/dev/null 2>&1; then
    # Удаляем старые правила для qBittorrent
    sudo ufw delete allow from 192.168.0.0/16 to any port 8080 proto tcp 2>/dev/null || true
    sudo ufw delete allow from 192.168.0.0/16 to any port 6881 2>/dev/null || true
    
    # Добавляем новые правила для TorrServer
    sudo ufw allow from 192.168.0.0/16 to any port 8090 proto tcp
    
    echo "✅ UFW правила обновлены"
else
    echo "⚠️  UFW не установлен, обновите правила вручную"
fi

# Запускаем обновленные сервисы
echo "🚀 Запуск обновленных сервисов..."
cd services
docker compose up -d
cd ..
check_success "Сервисы запущены"

# Ждем запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 15

# Проверяем статус
echo "🔍 Проверка статуса..."
cd services
docker compose ps
cd ..

# Проверяем доступность TorrServer
echo "🌐 Проверка доступности TorrServer..."
    if curl -f http://${HOMELAB_HOST:-your_local_ip}:8090 >/dev/null 2>&1; then
        echo "✅ TorrServer доступен по адресу: http://${HOMELAB_HOST:-your_local_ip}:8090"
else
    echo "⚠️  TorrServer не отвечает, проверьте логи:"
    echo "   docker compose -f services/docker-compose.yml logs torrserver"
fi

echo ""
echo "🎉 Миграция завершена!"
echo ""
echo "📋 Что изменилось:"
echo "   - qBittorrent заменен на TorrServer"
echo "   - Порт изменен с 8080 на 8090"
echo "   - Конфигурация обновлена"
echo "   - UFW правила обновлены"
echo ""
echo "🌐 Новые адреса:"
    echo "   - TorrServer: http://${HOMELAB_HOST:-your_local_ip}:8090"
    echo "   - Jellyfin: http://${HOMELAB_HOST:-your_local_ip}:8096"
    echo "   - Immich: http://${HOMELAB_HOST:-your_local_ip}:2283"
    echo "   - Vaultwarden: http://${HOMELAB_HOST:-your_local_ip}:8081"
    echo "   - Uptime Kuma: http://${HOMELAB_HOST:-your_local_ip}:3001"
    echo "   - Homelab Agent: http://${HOMELAB_HOST:-your_local_ip}:8000"
echo ""
echo "📁 Резервные копии:"
echo "   - docker-compose.yml: services/docker-compose.yml.backup.*"
echo "   - qBittorrent config: backups/qbittorrent_*"
echo ""
echo "🔧 Полезные команды:"
echo "   docker compose -f services/docker-compose.yml logs -f torrserver"
echo "   docker compose -f services/docker-compose.yml restart torrserver"
echo "   ./scripts/check_status.sh"
echo ""
echo "📚 Документация TorrServer:"
echo "   https://github.com/YouROK/TorrServer"

