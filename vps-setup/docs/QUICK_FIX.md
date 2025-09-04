# 🚀 Быстрое исправление Telegram API

## Проблема
```
HTTP/1.1 400 Bad Request
Failed to send message to Telegram
```

## Быстрое решение (1 команда)

```bash
chmod +x fix_quotes.sh && ./fix_quotes.sh
```

## Ручное исправление

### 1. Исправьте .env файл
```bash
# Уберите кавычки из значений
sed -i 's/^TELEGRAM_CHAT_ID="\([^"]*\)"$/TELEGRAM_CHAT_ID=\1/' .env
sed -i 's/^TELEGRAM_BOT_TOKEN="\([^"]*\)"$/TELEGRAM_BOT_TOKEN=\1/' .env
```

### 2. Перезапустите сервисы
```bash
sudo systemctl restart nginx php8.2-fpm
```

### 3. Протестируйте
```bash
php test_telegram.php
```

## Проверка статуса

```bash
# Проверка конфигурации
php check_config.php

# Тестирование длины сообщений
php test_message_length.php

# Просмотр логов
tail -f logs/homelab-vps.log
```

## Что исправлено

✅ **Кавычки в .env** - автоматически убираются  
✅ **Длина сообщений** - обрезка до 4000 символов  
✅ **Разбивка на части** - для очень длинных сообщений  
✅ **Умная разбивка** - по смысловым блокам  
✅ **Задержка между частями** - 1 секунда  
✅ **Улучшенное логирование** - детальная диагностика  
✅ **Обработка ошибок** - понятные сообщения об ошибках  

## Если не помогло

1. Проверьте логи: `tail -f logs/homelab-vps.log`
2. Проверьте nginx: `sudo tail -f /var/log/nginx/error.log`
3. Проверьте php-fpm: `sudo tail -f /var/log/php8.2-fpm.log`
4. Убедитесь, что бот добавлен в чат
5. Проверьте доступность api.telegram.org
