#!/usr/bin/env bash
set -euo pipefail

# Скрипт для настройки SSH туннеля через VPS

echo "🔧 Настройка SSH туннеля для GitHub webhook"

# Проверяем наличие SSH
if ! command -v ssh &> /dev/null; then
    echo "❌ SSH не установлен. Установите: sudo apt install openssh-client"
    exit 1
fi

# Запрашиваем информацию о VPS
echo "📋 Настройка SSH туннеля:"
read -p "IP адрес или домен VPS: " VPS_HOST
read -p "Пользователь на VPS: " VPS_USER
read -p "Порт SSH [22]: " VPS_PORT
VPS_PORT=${VPS_PORT:-22}

read -p "Домен для webhook (например: agent.yourdomain.com): " WEBHOOK_DOMAIN

if [ -z "$VPS_HOST" ] || [ -z "$VPS_USER" ] || [ -z "$WEBHOOK_DOMAIN" ]; then
    echo "❌ Все поля обязательны"
    exit 1
fi

# Создаем директорию для конфигурации
CONFIG_DIR="$(dirname "$0")/../ssh-tunnel"
mkdir -p "$CONFIG_DIR"

# Создаем скрипт для установки туннеля
echo "📝 Создание скрипта SSH туннеля..."

cat > "$CONFIG_DIR/setup_tunnel.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

# Конфигурация
VPS_HOST="$VPS_HOST"
VPS_USER="$VPS_USER"
VPS_PORT="$VPS_PORT"
WEBHOOK_DOMAIN="$WEBHOOK_DOMAIN"
LOCAL_PORT=8000
REMOTE_PORT=8000

echo "🔗 Создание SSH туннеля..."
echo "VPS: \$VPS_USER@\$VPS_HOST:\$VPS_PORT"
echo "Домен: \$WEBHOOK_DOMAIN"
echo "Локальный порт: \$LOCAL_PORT"
echo "Удаленный порт: \$REMOTE_PORT"

# Создаем туннель
ssh -f -N -R \$REMOTE_PORT:localhost:\$LOCAL_PORT \$VPS_USER@\$VPS_HOST -p \$VPS_PORT

echo "✅ SSH туннель создан"
echo "🌐 Webhook URL: https://\$WEBHOOK_DOMAIN/webhook/github"
EOF

chmod +x "$CONFIG_DIR/setup_tunnel.sh"

# Создаем скрипт для настройки nginx на VPS
echo "📝 Создание конфигурации nginx для VPS..."

cat > "$CONFIG_DIR/nginx_config.conf" <<EOF
# Конфигурация nginx для VPS
# Скопируйте этот файл в /etc/nginx/sites-available/agent-webhook

server {
    listen 80;
    server_name $WEBHOOK_DOMAIN;
    
    # Перенаправление на HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $WEBHOOK_DOMAIN;
    
    # SSL сертификаты (настройте Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/$WEBHOOK_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$WEBHOOK_DOMAIN/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Проксирование на локальный порт
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Создаем скрипт для настройки VPS
echo "📝 Создание скрипта настройки VPS..."

cat > "$CONFIG_DIR/setup_vps.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail

# Скрипт для настройки VPS
# Запустите этот скрипт на вашем VPS

echo "🔧 Настройка VPS для GitHub webhook"

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем nginx
sudo apt install nginx -y

# Устанавливаем certbot для SSL
sudo apt install certbot python3-certbot-nginx -y

# Копируем конфигурацию nginx
sudo cp nginx_config.conf /etc/nginx/sites-available/agent-webhook
sudo ln -sf /etc/nginx/sites-available/agent-webhook /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
sudo nginx -t

# Перезапускаем nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Получаем SSL сертификат
sudo certbot --nginx -d $WEBHOOK_DOMAIN

echo "✅ VPS настроен"
echo "🌐 Webhook URL: https://$WEBHOOK_DOMAIN/webhook/github"
EOF

chmod +x "$CONFIG_DIR/setup_vps.sh"

# Создаем systemd сервис для автоматического туннеля
echo "🔧 Создание systemd сервиса для SSH туннеля..."

sudo tee /etc/systemd/system/ssh-tunnel-agent.service > /dev/null <<EOF
[Unit]
Description=SSH tunnel for homelab agent
After=network.target

[Service]
Type=simple
User=$(whoami)
ExecStart=/usr/bin/ssh -N -R 8000:localhost:8000 $VPS_USER@$VPS_HOST -p $VPS_PORT
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Включаем и запускаем сервис
echo "🚀 Запуск SSH туннеля..."
sudo systemctl daemon-reload
sudo systemctl enable ssh-tunnel-agent.service

echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте файлы на VPS:"
echo "   scp $CONFIG_DIR/nginx_config.conf $VPS_USER@$VPS_HOST:~/"
echo "   scp $CONFIG_DIR/setup_vps.sh $VPS_USER@$VPS_HOST:~/"
echo ""
echo "2. На VPS запустите:"
echo "   chmod +x setup_vps.sh"
echo "   ./setup_vps.sh"
echo ""
echo "3. Запустите туннель:"
echo "   sudo systemctl start ssh-tunnel-agent.service"
echo ""
echo "4. Настройте webhook в GitHub:"
echo "   URL: https://$WEBHOOK_DOMAIN/webhook/github"
echo ""
echo "🎉 Настройка SSH туннеля завершена!"
