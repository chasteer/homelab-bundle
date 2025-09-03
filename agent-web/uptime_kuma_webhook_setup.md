# Настройка вебхука Uptime Kuma для Homelab Agent

## 🚀 Что мы настроили

1. **Новые тулы агента:**
   - `monitor_uptime_kuma()` - получение статуса мониторинга
   - `send_uptime_alert()` - отправка уведомлений на VPS
   - `generate_uptime_report()` - генерация отчета с рекомендациями

2. **Вебхук эндпоинт:** `/api/webhook/uptime-kuma`

## 📱 Настройка в Uptime Kuma

### Шаг 1: Создание уведомления
1. Войдите в Uptime Kuma: http://your_local_ip:3001
2. Перейдите в **Settings** → **Notifications**
3. Нажмите **"Add New Notification"**

### Шаг 2: Настройка вебхука
1. **Type:** Webhook
2. **Name:** Homelab Agent Webhook
3. **URL:** `http://your_local_ip:8000/api/webhook/uptime-kuma`
4. **Method:** POST
5. **Content Type:** application/json

### Шаг 3: Настройка триггеров
- **When monitor goes down:** ✅
- **When monitor goes up:** ✅ (опционально)
- **When monitor goes into maintenance:** ✅ (опционально)

### Шаг 4: Тестирование
1. Сохраните уведомление
2. Нажмите **"Test"** для проверки
3. Проверьте логи агента

## 🔧 Использование новых тулов

### Мониторинг статуса
```
Какой статус у мониторинга Uptime Kuma?
```

### Генерация отчета
```
Сгенерируй отчет о состоянии системы
```

### Отправка уведомления
```
Отправь уведомление о проблеме с сервисом Jellyfin
```

## 📡 Интеграция с VPS

Агент будет автоматически отправлять уведомления на:
- **URL:** `https://your_vps_domain.com/api/uptime-alerts`
- **Формат:** JSON с деталями проблемы
- **Данные:** название сервиса, статус, детали, временная метка

## 🚨 Пример уведомления

```json
{
  "source": "homelab_uptime_kuma",
  "timestamp": "2025-09-03T22:45:00",
  "service": "Jellyfin",
  "status": "down",
  "details": {
    "monitor_name": "Jellyfin Media Server",
    "monitor_url": "http://your_local_ip:8096",
    "status": "down",
    "alert_type": "down",
    "message": "Monitor is down",
    "datetime": "2025-09-03T22:45:00",
    "monitor_type": "http",
    "hostname": "your_local_ip",
    "port": 8096
  },
  "host": "your_local_ip",
  "webhook_type": "uptime_kuma"
}
```

## 🔍 Проверка работы

1. **Проверьте вебхук:** `GET http://your_local_ip:8000/api/webhook/uptime-kuma/health`
2. **Проверьте логи агента:** `docker logs homelab-agent`
3. **Тестируйте уведомления:** временно остановите любой сервис

## 📋 Следующие шаги

1. ✅ Настроить вебхук в Uptime Kuma
2. 🔄 Протестировать интеграцию
3. 🚀 Настроить VPS для приема уведомлений
4. 📱 Настроить Telegram бота
5. 🎯 Автоматизация действий по устранению проблем
