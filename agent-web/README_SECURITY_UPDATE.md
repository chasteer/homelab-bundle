# 🔒 Обновление безопасности - Homelab Agent

## 🚨 Что было исправлено

### 1. Убраны жестко закодированные IP адреса
**Было:**
```python
KUMA_URL = "http://your_local_ip:3001"
VPS_URL = "https://your_vps_domain.com/api/uptime-alerts"
host = "your_local_ip"
```

**Стало:**
```python
KUMA_URL = os.environ.get("UPTIME_KUMA_URL", "http://localhost:3001")
VPS_URL = os.environ.get("VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts")
host = os.environ.get("HOMELAB_HOST", "localhost")
```

### 2. Обновлены файлы
- ✅ `webhook_uptime.py` - все URL в переменных окружения
- ✅ `agent/tools.py` - IP адреса из переменных окружения
- ✅ `setup_uptime_webhook.py` - динамические URL
- ✅ `docker-compose.yml` - переменные окружения для всех настроек
- ✅ `UPTIME_KUMA_INTEGRATION.md` - обновлена документация

## 🛡️ Новые переменные окружения

### Обязательные переменные
```bash
# Сетевые настройки
HOMELAB_HOST=your_local_ip_here
UPTIME_KUMA_URL=http://your_local_ip:3001
AGENT_WEBHOOK_URL=http://your_local_ip:8000/api/webhook/uptime-kuma

# VPS настройки
VPS_WEBHOOK_URL=https://your_vps_domain.com/api/uptime-alerts
```

### Переменные с значениями по умолчанию
```bash
# Безопасные значения по умолчанию
HOMELAB_HOST=${HOMELAB_HOST:-localhost}
UPTIME_KUMA_URL=${UPTIME_KUMA_URL:-http://localhost:3001}
VPS_WEBHOOK_URL=${VPS_WEBHOOK_URL:-https://your_vps_domain.com/api/uptime-alerts}
```

## 🚀 Автоматическая настройка

### Скрипт определения IP
```bash
python3 get_system_ip.py
```

**Что делает:**
1. Автоматически определяет IP адреса системы
2. Создает файл `.env` с рекомендуемыми настройками
3. Предлагает оптимальные значения для вашей сети

### Пример вывода
```
🔍 Определение IP адресов системы...
📱 Локальный IP: your_local_ip
🌐 IP интерфейса: your_local_ip
🌍 Внешний IP: your_external_ip

💡 Рекомендуемый IP для HOMELAB_HOST: your_local_ip
```

## 📁 Структура файлов безопасности

```
agent-web/
├── .env                    # Ваши реальные настройки (НЕ коммитить!)
├── env.example            # Пример настроек
├── get_system_ip.py       # Автоматическое определение IP
├── SECURITY_BEST_PRACTICES.md  # Руководство по безопасности
└── README_SECURITY_UPDATE.md   # Этот файл
```

## 🔧 Настройка после обновления

### 1. Создайте .env файл
```bash
# Автоматически
python3 get_system_ip.py

# Или вручную
cp env.example .env
# Отредактируйте .env с вашими реальными значениями
```

### 2. Заполните обязательные поля
```bash
# API ключи
GIGACHAT_CREDENTIALS=your_real_credentials
TAVILY_API_KEY=your_real_api_key
GITHUB_TOKEN=your_real_token

# Сетевые настройки
HOMELAB_HOST=your_local_ip
UPTIME_KUMA_URL=http://your_ip:3001
VPS_WEBHOOK_URL=https://your_vps.com/api/endpoint
```

### 3. Перезапустите сервисы
```bash
sudo docker compose down
sudo docker compose up -d --build
```

## ✅ Проверка безопасности

### Автоматическая проверка
```bash
python3 get_system_ip.py
```

### Ручная проверка
1. Убедитесь, что в коде нет жестко закодированных IP
2. Проверьте, что все API ключи в .env
3. Убедитесь, что .env не в git
4. Проверьте права доступа к файлам

## 🚨 Важные напоминания

### 1. Никогда не коммитьте .env
```gitignore
# .gitignore
.env
*.env
.env.local
.env.prod
```

### 2. Используйте разные .env для разных сред
```bash
.env.dev      # Разработка
.env.prod     # Продакшн (НЕ коммитить!)
.env.test     # Тестирование
```

### 3. Регулярно обновляйте зависимости
```bash
pip install --upgrade -r requirements.txt
docker compose pull
```

## 🔍 Мониторинг безопасности

### Логирование
Все вебхуки и запросы логируются с IP адресами:
```python
logging.info(f"Webhook received from {request.client.host}")
```

### Алерты
Настройте уведомления о:
- Подозрительных IP адресах
- Множественных неудачных попытках
- Необычной активности

## 📚 Дополнительные ресурсы

- [SECURITY_BEST_PRACTICES.md](SECURITY_BEST_PRACTICES.md) - Подробное руководство по безопасности
- [UPTIME_KUMA_INTEGRATION.md](UPTIME_KUMA_INTEGRATION.md) - Интеграция с Uptime Kuma
- [env.example](env.example) - Пример настроек

## 🎯 Результат

Теперь ваш Homelab Agent:
- ✅ **Безопасен** - все чувствительные данные в переменных окружения
- ✅ **Гибок** - легко настраивается для разных сред
- ✅ **Автоматизирован** - IP адреса определяются автоматически
- ✅ **Документирован** - полные инструкции по безопасности

## 🚀 Следующие шаги

1. ✅ Обновление безопасности завершено
2. 🔄 Настройте .env файл с вашими реальными значениями
3. 🚀 Протестируйте интеграцию с Uptime Kuma
4. 📱 Настройте VPS и Telegram бота

Безопасность - это процесс, а не одноразовое действие! 🔒✨
