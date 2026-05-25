# 🏠 Homelab VPS - Telegram Integration

Интеграция Telegram бота для мониторинга Homelab сервисов через VPS.

## 🚀 Возможности

- ✅ **Автоматические уведомления** о статусе сервисов
- ✅ **Умная разбивка длинных сообщений** (Telegram limit: 4096 символов)
- ✅ **Краткий анализ инцидентов** от Cursor CLI (через Homelab Agent)
- ✅ **Безопасная конфигурация** через переменные окружения
- ✅ **Детальное логирование** всех операций
- ✅ **Автоматическое исправление** проблем с конфигурацией

## 📋 Требования

- PHP 8.0+
- Nginx + PHP-FPM
- Telegram Bot Token
- Telegram Chat ID

## 🛠️ Установка

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd vps-setup
```

### 2. Настройка конфигурации
```bash
# Создайте .env файл из примера
cp env.example .env

# Отредактируйте .env файл
nano .env
```

### 3. Заполните обязательные поля в .env
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**⚠️ ВАЖНО:** Не ставьте кавычки вокруг значений!

### 4. Настройка прав доступа
```bash
chmod 644 .env
chmod 644 api/*.php
chown www-data:www-data .env
chown www-data:www-data api/*.php
```

### 5. Создание директории для логов
```bash
mkdir -p logs
chmod 755 logs
chown www-data:www-data logs
```

### 6. Перезапуск веб-сервера
```bash
sudo systemctl restart nginx
sudo systemctl restart php8.2-fpm
```

## 🧪 Тестирование

### Автоматическое тестирование
```bash
# Полное тестирование (рекомендуется)
chmod +x fix_quotes.sh
./fix_quotes.sh
```

### Ручное тестирование
```bash
# Проверка конфигурации
php check_config.php

# Тестирование Telegram API
php test_telegram.php

# Полное тестирование
php test_all.php
```

## 🔧 Использование

### API Endpoint
```
POST /api/uptime-alerts
Content-Type: application/json

{
  "source": "homelab_uptime_kuma",
  "service": "Jellyfin",
  "status": "down",
  "host": "192.168.1.200",
  "incident_analysis": "**Причина:** ...\n**Проверить:** ...",
  "analysis_type": "cursor_cli",
  "cursor_report_path": "/app/logs/incidents/....md",
  "details": {
    "monitor_url": "http://192.168.1.200:8096",
    "monitor_type": "http",
    "message": "..."
  }
}
```

Поле `incident_analysis` уже **сжато** на стороне агента (~1400 символов). VPS дополнительно обрезает анализ до ~1600 символов перед отправкой в Telegram.

### Автоматическая разбивка сообщений
Система разбивает длинные сообщения на части:
- Сообщения > 4000 символов
- Сообщения с `incident_analysis` (если агент прислал слишком длинный текст)
- Умная разбивка по смысловым блокам
- Задержка 1 секунда между частями

## 📁 Структура проекта

```
vps-setup/
├── api/                    # API файлы
│   ├── config.php         # Конфигурация
│   ├── telegram.php       # Telegram интеграция
│   ├── uptime-alerts.php  # Основной endpoint
│   └── status.php         # Статус сервиса
├── scripts/               # Скрипты настройки
│   ├── fix_quotes.sh      # Исправление кавычек
│   └── setup_telegram.sh  # Настройка Telegram
├── docs/                  # Документация
│   ├── TELEGRAM_FIX.md    # Инструкция по исправлению
│   ├── QUICK_FIX.md       # Быстрое исправление
│   └── LONG_MESSAGES_GUIDE.md # Руководство по длинным сообщениям
├── .env.example           # Пример конфигурации
├── .gitignore            # Исключения Git
└── README.md             # Этот файл
```

## 🔍 Диагностика

### Проверка логов
```bash
# Логи приложения
tail -f logs/homelab-vps.log

# Логи nginx
sudo tail -f /var/log/nginx/error.log

# Логи php-fpm
sudo tail -f /var/log/php8.2-fpm.log
```

### Проверка конфигурации
```bash
php check_config.php
```

## 🚨 Устранение неполадок

### Проблема: "message text is empty"
1. Проверьте наличие файла `.env`
2. Убедитесь, что значения не в кавычках
3. Запустите: `./fix_quotes.sh`

### Проблема: "Failed to send message to Telegram"
1. Проверьте правильность TELEGRAM_BOT_TOKEN
2. Убедитесь, что бот добавлен в чат
3. Проверьте TELEGRAM_CHAT_ID

### Проблема: Длинные сообщения обрезаются
Система автоматически разбивает длинные сообщения на части. Если проблема остается, проверьте логи.

## 📚 Документация

- [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) — настройка бота
- [TELEGRAM_FIX.md](docs/TELEGRAM_FIX.md) — исправление типичных ошибок
- [QUICK_FIX.md](docs/QUICK_FIX.md) — быстрые исправления
- [LONG_MESSAGES_GUIDE.md](docs/LONG_MESSAGES_GUIDE.md) — длинные сообщения
- [../agent-web/INCIDENT_FLOW.md](../agent-web/INCIDENT_FLOW.md) — Cursor CLI на стороне homelab

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f logs/homelab-vps.log`
2. Запустите диагностику: `php check_config.php`
3. Создайте issue в репозитории

## 📄 Лицензия

MIT License - см. файл [LICENSE](../LICENSE)

---

**🎉 Telegram интеграция готова к работе!**
