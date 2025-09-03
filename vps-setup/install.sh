#!/bin/bash

# Homelab VPS Installation Script
# Запускайте на Ubuntu Server с PHP 8.4-FPM и Nginx

set -e

echo "🚀 Установка Homelab VPS API..."

# Проверяем, что мы root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен быть запущен от root"
   exit 1
fi

# Проверяем Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    echo "❌ Этот скрипт предназначен для Ubuntu"
    exit 1
fi

# Обновляем систему
echo "📦 Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
echo "📦 Устанавливаем необходимые пакеты..."
apt install -y curl wget git unzip

# Проверяем PHP
if ! command -v php8.4 &> /dev/null; then
    echo "❌ PHP 8.4 не установлен. Установите его вручную:"
    echo "sudo apt install php8.4-fpm php8.4-common php8.4-mysql php8.4-xml php8.4-curl php8.4-mbstring php8.4-zip"
    exit 1
fi

# Проверяем Nginx
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx не установлен. Установите его вручную:"
    echo "sudo apt install nginx"
    exit 1
fi

# Создаем директории
echo "📁 Создаем директории..."
mkdir -p /var/www/homelab-vps/{api,logs}
mkdir -p /var/log/nginx

# Копируем файлы
echo "📋 Копируем файлы..."
cp -r api/* /var/www/homelab-vps/api/
cp env.example /var/www/homelab-vps/.env

# Устанавливаем права
echo "🔐 Устанавливаем права..."
chown -R www-data:www-data /var/www/homelab-vps
chmod -R 755 /var/www/homelab-vps
chmod 640 /var/www/homelab-vps/.env

# Настраиваем Nginx
echo "🌐 Настраиваем Nginx..."
cp nginx.conf /etc/nginx/sites-available/homelab-vps

# Активируем сайт
ln -sf /etc/nginx/sites-available/homelab-vps /etc/nginx/sites-enabled/

# Удаляем дефолтный сайт если есть
if [[ -f /etc/nginx/sites-enabled/default ]]; then
    rm /etc/nginx/sites-enabled/default
fi

# Проверяем конфигурацию Nginx
echo "🔍 Проверяем конфигурацию Nginx..."
nginx -t

# Перезапускаем Nginx
echo "🔄 Перезапускаем Nginx..."
systemctl restart nginx
systemctl enable nginx

# Перезапускаем PHP-FPM
echo "🔄 Перезапускаем PHP-FPM..."
systemctl restart php8.4-fpm
systemctl enable php8.4-fpm

# Создаем тестовый endpoint
echo "🧪 Создаем тестовый endpoint..."
cat > /var/www/homelab-vps/api/test.php << 'EOF'
<?php
header('Content-Type: application/json');
echo json_encode([
    'status' => 'success',
    'message' => 'Homelab VPS API работает!',
    'timestamp' => date('c'),
    'php_version' => PHP_VERSION
]);
EOF

# Создаем статус endpoint
echo "📊 Создаем статус endpoint..."
cat > /var/www/homelab-vps/api/status.php << 'EOF'
<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/telegram.php';

header('Content-Type: application/json');

try {
    $botStatus = checkBotStatus();
    
    echo json_encode([
        'status' => 'success',
        'vps' => [
            'hostname' => gethostname(),
            'php_version' => PHP_VERSION,
            'nginx_status' => 'running',
            'php_fpm_status' => 'running'
        ],
        'telegram_bot' => $botStatus,
        'timestamp' => date('c')
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
EOF

# Создаем health check
echo "❤️ Создаем health check..."
cat > /var/www/homelab-vps/api/health.php << 'EOF'
<?php
header('Content-Type: application/json');

$status = 'healthy';
$checks = [];

// Проверяем PHP
$checks['php'] = 'ok';

// Проверяем права на запись в лог
$logFile = __DIR__ . '/../logs/homelab-vps.log';
$checks['logs_writable'] = is_writable(dirname($logFile)) ? 'ok' : 'error';

// Проверяем .env файл
$envFile = __DIR__ . '/../.env';
$checks['env_file'] = file_exists($envFile) ? 'ok' : 'error';

if (in_array('error', $checks)) {
    $status = 'unhealthy';
}

echo json_encode([
    'status' => $status,
    'checks' => $checks,
    'timestamp' => date('c')
]);
EOF

# Устанавливаем права на новые файлы
chown -R www-data:www-data /var/www/homelab-vps
chmod -R 755 /var/www/homelab-vps/api

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте /var/www/homelab-vps/.env"
echo "2. Создайте Telegram бота и получите токен"
echo "3. Получите Chat ID"
echo "4. Настройте SSL сертификат"
echo "5. Протестируйте API"
echo ""
echo "🌐 API endpoints:"
echo "- Тест: https://your-domain.com/api/test"
echo "- Статус: https://your-domain.com/api/status"
echo "- Здоровье: https://your-domain.com/api/health"
echo "- Webhook: https://your-domain.com/api/uptime-alerts"
echo ""
echo "📚 Документация: README.md"
echo "🔧 Настройка Telegram: TELEGRAM_SETUP.md"
