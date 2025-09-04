# 🔧 Исправление ошибки Telegram API

## Проблема
```
{"ok":false,"error_code":400,"description":"Bad Request: message text is empty"}
```

Или:
```
HTTP/1.1 400 Bad Request
Failed to send message to Telegram
```

## Причины
1. **Отсутствует файл `.env`** с настройками Telegram бота
2. **Лишние кавычки** в значениях переменных окружения
3. **Сообщение слишком длинное** (превышает лимит Telegram 4096 символов)
4. **Неправильный формат** TELEGRAM_CHAT_ID

## Решение

### 1. Создайте файл .env на VPS
```bash
cd /var/www/babeshin.ru/htdocs
cp env.example .env
```

### 2. Отредактируйте .env файл
```bash
nano .env
```

Заполните обязательные поля **БЕЗ КАВЫЧЕК**:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**⚠️ ВАЖНО:** Не ставьте кавычки вокруг значений!

### 3. Получите TELEGRAM_CHAT_ID
1. Добавьте бота в нужный чат
2. Отправьте любое сообщение в чат
3. Откройте в браузере: `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
4. Найдите `chat.id` в ответе

### 4. Проверьте права доступа
```bash
chmod 644 .env
chmod 644 api/*.php
chown www-data:www-data .env
chown www-data:www-data api/*.php
```

### 5. Создайте директорию для логов
```bash
mkdir -p logs
chmod 755 logs
chown www-data:www-data logs
```

### 6. Перезапустите веб-сервер
```bash
sudo systemctl restart nginx
sudo systemctl restart php8.2-fpm
```

### 7. Протестируйте
```bash
# Проверка конфигурации
php check_config.php

# Тестирование Telegram API
php test_telegram.php

# Тестирование длины сообщений
php test_message_length.php

# Тестирование длинных сообщений
php test_long_message.php
```

## Автоматическая настройка
Запустите скрипт настройки:
```bash
chmod +x setup_telegram.sh
./setup_telegram.sh
```

## Быстрое исправление кавычек
Если у вас проблема с кавычками в .env файле:
```bash
chmod +x fix_quotes.sh
./fix_quotes.sh
```

## Проверка логов
```bash
tail -f logs/homelab-vps.log
```

## Структура .env файла
```env
# Telegram Bot настройки
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Окружение
ENVIRONMENT=production

# Логирование
LOG_LEVEL=INFO
```

## Дополнительная диагностика
Если проблема остается, проверьте:
1. Активен ли Telegram бот
2. Правильно ли указан TELEGRAM_CHAT_ID (без кавычек!)
3. Есть ли доступ к api.telegram.org
4. Логи nginx и php-fpm

## Проверка текущего состояния
```bash
# Проверка конфигурации
php check_config.php

# Тестирование Telegram API
php test_telegram.php

# Проверка логов
tail -f logs/homelab-vps.log

# Проверка nginx
sudo tail -f /var/log/nginx/error.log

# Проверка php-fpm
sudo tail -f /var/log/php8.2-fpm.log
```

## Длинные сообщения

Теперь система автоматически разбивает длинные сообщения на несколько частей:

### Автоматическая разбивка
- Сообщения > 4000 символов разбиваются на части
- Задержка 1 секунда между частями
- Умная разбивка по смысловым блокам

### Тестирование
```bash
# Тестирование длинных сообщений
php test_long_message.php
```

### Подробное руководство
См. файл `LONG_MESSAGES_GUIDE.md` для детальной информации.
