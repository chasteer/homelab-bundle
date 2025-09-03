#!/usr/bin/env bash
set -euo pipefail

# Скрипт полного развертывания Homelab

echo "🚀 Полное развертывание Homelab..."
echo "=================================="

# Проверяем, что мы в корневой директории
if [ ! -f "README.md" ]; then
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

# Шаг 1: Bootstrap Ubuntu
echo ""
echo "🔧 Шаг 1: Подготовка системы..."
./scripts/00_bootstrap_ubuntu.sh
check_success "Bootstrap Ubuntu завершен"

# Шаг 2: Создание директорий
echo ""
echo "📁 Шаг 2: Создание директорий..."
./scripts/10_prepare_dirs.sh
check_success "Директории созданы"

# Шаг 3: Настройка переменных окружения
echo ""
echo "⚙️  Шаг 3: Настройка переменных окружения..."
if [ ! -f "services/.env" ]; then
    ./scripts/15_write_env.sh
    check_success "Переменные окружения настроены"
else
    echo "✅ services/.env уже существует"
fi

# Шаг 4: Развертывание основных сервисов
echo ""
echo "🐳 Шаг 4: Развертывание основных сервисов..."
./scripts/20_deploy_core.sh
check_success "Основные сервисы развернуты"

# Ждем запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Шаг 5: Развертывание агента
echo ""
echo "🤖 Шаг 5: Развертывание Homelab Agent..."
./scripts/40_deploy_agent_web.sh
check_success "Homelab Agent развернут"

# Шаг 6: Настройка UFW
echo ""
echo "🔒 Шаг 6: Настройка UFW..."
read -p "Настроить UFW? (y/n) [y]: " CONFIGURE_UFW
CONFIGURE_UFW=${CONFIGURE_UFW:-y}

if [ "$CONFIGURE_UFW" = "y" ] || [ "$CONFIGURE_UFW" = "Y" ]; then
    ./scripts/50_configure_ufw.sh
    check_success "UFW настроен"
else
    echo "⚠️  UFW не настроен. Настройте вручную: ./scripts/50_configure_ufw.sh"
fi

# Шаг 7: Настройка прокси (опционально)
echo ""
echo "🌐 Шаг 7: Настройка прокси (опционально)..."
echo "Выберите прокси сервер:"
echo "1. Caddy (HTTPS с Let's Encrypt)"
echo "2. Traefik (сложнее, но гибче)"
echo "3. Пропустить"

read -p "Ваш выбор [1]: " PROXY_CHOICE
PROXY_CHOICE=${PROXY_CHOICE:-1}

case $PROXY_CHOICE in
    1)
        echo "🔧 Настройка Caddy..."
        ./scripts/30_deploy_proxy_caddy.sh
        check_success "Caddy настроен"
        ;;
    2)
        echo "🔧 Настройка Traefik..."
        ./scripts/30_deploy_proxy_traefik.sh
        check_success "Traefik настроен"
        ;;
    3)
        echo "⚠️  Прокси не настроен"
        ;;
    *)
        echo "❌ Неверный выбор"
        ;;
esac

# Шаг 8: Настройка внешнего доступа (опционально)
echo ""
echo "🌍 Шаг 8: Настройка внешнего доступа (опционально)..."
echo "Выберите способ внешнего доступа:"
echo "1. ngrok (просто, но публично)"
echo "2. SSH туннель через VPS (безопасно, но сложнее)"
echo "3. Пропустить"

read -p "Ваш выбор [3]: " EXTERNAL_CHOICE
EXTERNAL_CHOICE=${EXTERNAL_CHOICE:-3}

case $EXTERNAL_CHOICE in
    1)
        echo "🔧 Настройка ngrok..."
        ./scripts/60_setup_ngrok.sh
        check_success "ngrok настроен"
        ;;
    2)
        echo "🔧 Настройка SSH туннеля..."
        ./scripts/80_setup_ssh_tunnel.sh
        check_success "SSH туннель настроен"
        ;;
    3)
        echo "⚠️  Внешний доступ не настроен"
        ;;
    *)
        echo "❌ Неверный выбор"
        ;;
esac

# Финальная проверка
echo ""
echo "🔍 Финальная проверка..."

# Проверяем основные сервисы
echo "📊 Статус основных сервисов:"
cd services && sudo docker compose ps && cd ..

# Проверяем агента
echo ""
echo "🤖 Статус Homelab Agent:"
cd agent-web && sudo docker compose ps && cd ..

# Проверяем сеть
echo ""
echo "🌐 Проверка сети homelab:"
sudo docker network ls | grep homelab

# Проверяем порты
echo ""
echo "🔌 Проверка открытых портов:"
netstat -tlnp | grep -E ':(8080|2283|8081|3001|8096|8000)' || echo "Порты не прослушиваются"

echo ""
echo "🎉 Развертывание Homelab завершено!"
echo ""
echo "📋 Доступные сервисы:"
echo "   🌐 Jellyfin: http://192.168.1.200:8096"
echo "   📥 qBittorrent: http://192.168.1.200:8080"
echo "   📸 Immich: http://192.168.1.200:2283"
echo "   🔐 Vaultwarden: http://192.168.1.200:8081"
echo "   📊 Uptime Kuma: http://192.168.1.200:3001"
echo "   🤖 Homelab Agent: http://192.168.1.200:8000"
echo ""
echo "📋 Полезные команды:"
echo "   ./scripts/agent_manage.sh status    # Статус агента"
echo "   ./scripts/agent_manage.sh logs      # Логи агента"
echo "   sudo docker compose -f services/docker-compose.yml ps  # Статус сервисов"
echo "   sudo docker compose -f agent-web/docker-compose.yml ps # Статус агента"
echo ""
echo "🔧 Для запуска GitHub polling:"
echo "   cd agent-web && sudo docker compose --profile polling up -d github-polling"
echo ""
echo "📚 Документация: agent-web/README.md"
