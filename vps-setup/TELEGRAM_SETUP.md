# 🤖 Настройка Telegram Bot для Homelab VPS

## 📋 Обзор

**Telegram Bot только получает уведомления** от Homelab Agent через VPS (в т.ч. краткий анализ от **Cursor CLI** при падении сервисов). Без команд и интерактивности.

Цепочка: [agent-web/INCIDENT_FLOW.md](../agent-web/INCIDENT_FLOW.md) → `VPS_WEBHOOK_URL` → этот бот.

## 🚀 Шаг 1: Создание Telegram Bot

### 1. Найдите @BotFather в Telegram
- Откройте Telegram
- Найдите пользователя `@BotFather`
- Отправьте команду `/start`

### 2. Создайте нового бота
```
/newbot
```

### 3. Следуйте инструкциям:
- Введите имя бота (например: "Homelab Monitor")
- Введите username бота (например: "homelab_monitor_bot")
- Получите токен бота

**Сохраните токен!** Он понадобится для настройки.

## 🔐 Шаг 2: Получение Chat ID

### Вариант 1: Личный чат
1. Отправьте сообщение вашему боту
2. Откройте в браузере:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Найдите `chat_id` в ответе

### Вариант 2: Групповой чат
1. Добавьте бота в группу
2. Отправьте сообщение в группу
3. Получите `chat_id` как в варианте 1

### Вариант 3: Канал
1. Добавьте бота в канал как администратора
2. Отправьте сообщение в канал
3. Получите `chat_id` (будет начинаться с `-100`)

## ⚙️ Шаг 3: Настройка VPS

### 1. Отредактируйте файл `.env`:
```bash
nano /var/www/homelab-vps/.env
```

### 2. Заполните настройки:
```env
# Telegram Bot настройки
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# API безопасность
API_SECRET_KEY=your_secret_key_here

# Окружение
ENVIRONMENT=production
```

### 3. Перезапустите PHP-FPM:
```bash
sudo systemctl restart php8.4-fpm
```

## 🧪 Шаг 4: Тестирование

### 1. Проверьте статус бота:
```bash
curl https://your-domain.com/api/status
```

### 2. Отправьте тестовое сообщение:
```bash
curl https://your-domain.com/api/test
```

### 3. Проверьте Telegram - должно прийти сообщение!

## 🔍 Шаг 5: Проверка логов

### Просмотр логов VPS:
```bash
tail -f /var/www/homelab-vps/logs/homelab-vps.log
```

### Просмотр логов Nginx:
```bash
tail -f /var/log/nginx/homelab-vps.access.log
tail -f /var/log/nginx/homelab-vps.error.log
```

## 🚨 Устранение неполадок

### Проблема: Bot token не работает
**Решение:**
1. Проверьте правильность токена
2. Убедитесь, что бот не заблокирован
3. Проверьте права бота в чате

### Проблема: Сообщения не приходят
**Решение:**
1. Проверьте Chat ID
2. Убедитесь, что бот добавлен в чат
3. Проверьте логи VPS

### Проблема: API возвращает ошибки
**Решение:**
1. Проверьте права на файлы
2. Проверьте конфигурацию Nginx
3. Проверьте логи PHP

## 📱 Примеры сообщений

### Уведомление о падении сервиса:
```
🚨 **HOMELAB ALERT** 🚨

**Service:** TorrServer
**Status:** Down
**Host:** your-local-ip
**Time:** 2025-09-04 00:30:00 +00:00

**Details:**
• monitor_name: TorrServer
• monitor_url: http://your-local-ip:8090
• alert_type: down
• message: Service is down
```

### Уведомление о восстановлении:
```
✅ **HOMELAB ALERT** ✅

**Service:** TorrServer
**Status:** Up
**Host:** your-local-ip
**Time:** 2025-09-04 00:35:00 +00:00

**Details:**
• monitor_name: TorrServer
• monitor_url: http://your-local-ip:8090
• alert_type: up
• message: Service is up
```

## 🔒 Безопасность

### Рекомендации:
1. **Не публикуйте токен бота** в открытых репозиториях
2. **Используйте HTTPS** для всех API вызовов
3. **Настройте API ключ** для дополнительной защиты
4. **Ограничьте доступ** по IP адресам если возможно

## ⚠️ Важно помнить

**Этот бот предназначен ТОЛЬКО для получения уведомлений. Он не будет:**
- ❌ Отвечать на команды
- ❌ Выполнять действия
- ❌ Интерактивить с пользователями
- ❌ Обрабатывать входящие сообщения

**Бот только отправляет уведомления о состоянии сервисов Homelab!**

## 📚 Дополнительные ресурсы

- [Telegram Bot API документация](https://core.telegram.org/bots/api)
- [BotFather команды](https://core.telegram.org/bots#botfather)

---

**Готово! Теперь ваш Telegram Bot будет получать все уведомления от Homelab без лишней интерактивности!** 🎉
