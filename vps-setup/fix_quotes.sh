#!/bin/bash

# Скрипт для исправления кавычек в .env файле
# Запускайте на VPS сервере

echo "🔧 Исправление кавычек в .env файле"
echo "=================================="

# Проверяем, что мы в правильной директории
if [ ! -f ".env" ]; then
    echo "❌ Ошибка: Файл .env не найден"
    echo "Создайте файл .env из env.example"
    exit 1
fi

echo "📝 Текущий .env файл:"
echo "---------------------"
cat .env
echo "---------------------"

# Создаем backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup создан"

# Исправляем кавычки
echo ""
echo "🔧 Исправляю кавычки..."

# Убираем лишние кавычки из TELEGRAM_CHAT_ID
sed -i 's/^TELEGRAM_CHAT_ID="\([^"]*\)"$/TELEGRAM_CHAT_ID=\1/' .env

# Убираем лишние кавычки из TELEGRAM_BOT_TOKEN
sed -i 's/^TELEGRAM_BOT_TOKEN="\([^"]*\)"$/TELEGRAM_BOT_TOKEN=\1/' .env

echo "✅ Кавычки исправлены"

echo ""
echo "📝 Исправленный .env файл:"
echo "--------------------------"
cat .env
echo "--------------------------"

echo ""
echo "🔄 Перезапускаю веб-сервер..."
sudo systemctl restart nginx
sudo systemctl restart php8.2-fpm

echo ""
echo "🧪 Тестирую исправление..."
php test_telegram.php

echo ""
echo "🧪 Тестирую длину сообщений..."
php test_message_length.php

echo ""
echo "🧪 Тестирую длинные сообщения..."
php test_long_message.php

echo ""
echo "🧪 Полное тестирование..."
php test_all.php

echo ""
echo "✅ Исправление завершено!"
echo "📋 Если проблема остается, проверьте:"
echo "1. Логи nginx: sudo tail -f /var/log/nginx/error.log"
echo "2. Логи php-fpm: sudo tail -f /var/log/php8.2-fpm.log"
echo "3. Логи приложения: tail -f logs/homelab-vps.log"
