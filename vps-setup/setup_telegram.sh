#!/bin/bash

# Скрипт настройки Telegram бота для Homelab VPS
# Запускайте на VPS сервере

set -e

echo "🔧 Настройка Telegram бота для Homelab VPS"
echo "=========================================="

# Проверяем, что мы в правильной директории
if [ ! -f "api/config.php" ]; then
    echo "❌ Ошибка: Запустите скрипт из директории vps-setup"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "📝 Создаю файл .env из примера..."
    cp env.example .env
    echo "✅ Файл .env создан"
    echo ""
    echo "⚠️  ВАЖНО: Отредактируйте файл .env и заполните:"
    echo "   - TELEGRAM_BOT_TOKEN (токен вашего бота)"
    echo "   - TELEGRAM_CHAT_ID (ID чата для уведомлений)"
    echo ""
    echo "📖 Инструкция по настройке в файле TELEGRAM_SETUP.md"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
else
    echo "✅ Файл .env уже существует"
fi

# Проверяем настройки
echo ""
echo "🔍 Проверяю настройки..."

# Загружаем переменные из .env
source <(grep -E '^[A-Z_]+=' .env | sed 's/^/export /')

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ TELEGRAM_CHAT_ID не настроен"
    exit 1
fi

echo "✅ TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "✅ TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID"

# Создаем директорию для логов
echo ""
echo "📁 Создаю директорию для логов..."
mkdir -p logs
chmod 755 logs

# Проверяем права на файлы
echo ""
echo "🔐 Проверяю права доступа..."
chmod 644 .env
chmod 644 api/*.php

# Тестируем API
echo ""
echo "🧪 Тестирую API..."
curl -X POST "http://localhost/api/uptime-alerts" \
     -H "Content-Type: application/json" \
     -d '{
       "source": "test",
       "service": "test-service",
       "status": "up",
       "host": "test-host",
       "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
     }' || echo "❌ API тест не прошел (это нормально если сервис не запущен)"

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Убедитесь, что ваш Telegram бот активен"
echo "2. Проверьте, что бот добавлен в нужный чат"
echo "3. Перезапустите веб-сервер (nginx + php-fpm)"
echo "4. Протестируйте отправку уведомления"
echo ""
echo "📖 Подробная инструкция: TELEGRAM_SETUP.md"
