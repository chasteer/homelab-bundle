#!/usr/bin/env bash
set -euo pipefail

# Скрипт для настройки ngrok туннеля для GitHub webhook

echo "🔧 Настройка ngrok туннеля для GitHub webhook"

# Проверяем, установлен ли ngrok
if ! command -v ngrok &> /dev/null; then
    echo "📦 Установка ngrok..."
    
    # Определяем архитектуру
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="arm" ;;
        *) echo "❌ Неподдерживаемая архитектура: $ARCH"; exit 1 ;;
    esac
    
    # Скачиваем ngrok
    wget -O /tmp/ngrok.zip "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-${ARCH}.zip"
    
    # Устанавливаем
    sudo unzip /tmp/ngrok.zip -d /usr/local/bin/
    sudo chmod +x /usr/local/bin/ngrok
    rm /tmp/ngrok.zip
    
    echo "✅ ngrok установлен"
else
    echo "✅ ngrok уже установлен"
fi

# Проверяем auth token
if [ -z "${NGROK_AUTH_TOKEN:-}" ]; then
    echo "🔑 Получение auth token для ngrok..."
    echo "1. Перейдите на https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Скопируйте ваш auth token"
    read -p "Введите ваш ngrok auth token: " NGROK_AUTH_TOKEN
fi

# Настраиваем ngrok
ngrok config add-authtoken "$NGROK_AUTH_TOKEN"

# Запрашиваем дополнительные настройки безопасности
echo "🔒 Настройка безопасности:"
read -p "Добавить базовую аутентификацию? (y/n) [n]: " USE_AUTH
if [ "$USE_AUTH" = "y" ] || [ "$USE_AUTH" = "Y" ]; then
    read -p "Имя пользователя: " AUTH_USER
    read -s -p "Пароль: " AUTH_PASS
    echo
    AUTH_OPTION="--basic-auth=\"$AUTH_USER:$AUTH_PASS\""
else
    AUTH_OPTION=""
fi

read -p "Включить логирование? (y/n) [y]: " USE_LOGS
if [ "$USE_LOGS" = "n" ] || [ "$USE_LOGS" = "N" ]; then
    LOG_OPTION=""
else
    LOG_OPTION="--log=stdout"
fi

# Создаем systemd сервис
echo "🔧 Создание systemd сервиса..."

sudo tee /etc/systemd/system/ngrok-agent.service > /dev/null <<EOF
[Unit]
Description=ngrok tunnel for homelab agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=$(whoami)
ExecStart=/usr/local/bin/ngrok http ${HOMELAB_HOST:-your_local_ip}:8000 $AUTH_OPTION $LOG_OPTION
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создаем скрипт для получения URL туннеля
echo "📝 Создание скрипта для получения URL туннеля..."

cat > "$(dirname "$0")/get_tunnel_url.sh" <<'EOF'
#!/usr/bin/env bash

# Получаем URL из ngrok API
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)

if [ "$TUNNEL_URL" != "null" ] && [ -n "$TUNNEL_URL" ]; then
    echo "🌐 Туннель активен: $TUNNEL_URL"
    echo "🔗 Webhook URL: $TUNNEL_URL/webhook/github"
    echo ""
    echo "📋 Настройте webhook в GitHub:"
    echo "   Payload URL: $TUNNEL_URL/webhook/github"
    echo "   Content type: application/json"
    echo "   Events: Pull requests"
else
    echo "❌ Туннель не активен. Проверьте статус:"
    echo "   sudo systemctl status ngrok-agent"
fi
EOF

chmod +x "$(dirname "$0")/get_tunnel_url.sh"

# Включаем и запускаем сервис
echo "🚀 Запуск ngrok сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable ngrok-agent.service
sudo systemctl start ngrok-agent.service

# Ждем запуска
echo "⏳ Ожидание запуска туннеля..."
sleep 5

# Проверяем статус
if sudo systemctl is-active --quiet ngrok-agent.service; then
    echo "✅ ngrok сервис запущен"
    
    # Показываем URL туннеля
    echo ""
    echo "🔍 Получение URL туннеля..."
    "$(dirname "$0")/get_tunnel_url.sh"
    
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Скопируйте webhook URL выше"
    echo "2. Настройте webhook в GitHub репозитории"
    echo "3. Используйте скрипт get_tunnel_url.sh для получения URL в будущем"
    
else
    echo "❌ Ошибка запуска ngrok сервиса"
    echo "Проверьте логи: sudo journalctl -u ngrok-agent.service"
    exit 1
fi

echo ""
echo "🎉 Настройка ngrok завершена!"
echo ""
echo "🔒 Рекомендации по безопасности:"
echo "1. Используйте сильный GITHUB_WEBHOOK_SECRET"
echo "2. Регулярно обновляйте секреты"
echo "3. Мониторьте логи: sudo journalctl -u ngrok-agent.service"
echo "4. Останавливайте туннель когда не нужен"
echo "5. Рассмотрите использование ngrok с аутентификацией"
echo ""
echo "⚠️  Важно: URL туннеля публичный - не делитесь им с посторонними!"
