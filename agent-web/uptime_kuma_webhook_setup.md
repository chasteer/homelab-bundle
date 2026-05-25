# Настройка webhook Uptime Kuma → Homelab Incident Service

## Цепочка

1. Монитор в Uptime Kuma переходит в **Down**
2. Uptime Kuma шлёт **POST** на агент
3. Агент вызывает **Cursor CLI** (краткий анализ репозитория homelab)
4. Агент шлёт JSON на **VPS** → **Telegram**

## Предварительные условия

- Запущены `uptime-kuma` и `homelab-agent` в сети Docker `homelab`
- В `agent-web/.env`: `CURSOR_API_KEY`, `VPS_WEBHOOK_URL`, `HOMELAB_HOST`
- VPS и Telegram настроены: [vps-setup/TELEGRAM_SETUP.md](../vps-setup/TELEGRAM_SETUP.md)

## Шаг 1: Проверка агента

```bash
curl -s http://<HOMELAB_HOST>:8000/api/webhook/uptime-kuma/health
curl -X POST http://<HOMELAB_HOST>:8000/api/webhook/uptime-kuma/test-cursor
```

Ожидается `"analysis_type": "cursor_cli"`.

## Шаг 2: Уведомление в Uptime Kuma

1. Откройте Uptime Kuma: `http://<HOMELAB_HOST>:3001`
2. **Settings** → **Notifications** → **Add New Notification**
3. Параметры:
   - **Type:** Webhook
   - **Friendly Name:** Homelab Agent
   - **URL:** `http://<HOMELAB_HOST>:8000/api/webhook/uptime-kuma`
   - **Method:** POST
   - **Content Type:** application/json
4. Триггеры:
   - **Down** — обязательно (запускает Cursor CLI)
   - **Up** — по желанию (короткое сообщение о восстановлении)
5. **Test** — в логах агента: `docker compose logs -f agent`

## Шаг 3: Привязка к мониторам

В каждом мониторе → **Notifications** → включите созданное уведомление.

## Формат на VPS / Telegram

Агент отправляет на `VPS_WEBHOOK_URL`:

```json
{
  "source": "homelab_uptime_kuma",
  "service": "Jellyfin",
  "status": "down",
  "incident_analysis": "**Причина:** ...\n**Проверить:** ...",
  "analysis_type": "cursor_cli",
  "cursor_report_path": "/app/logs/incidents/....md",
  "details": { "monitor_url": "...", "monitor_type": "http", "message": "..." }
}
```

Текст в Telegram **сжат** (~1400 символов). Полный отчёт — в `agent-web/logs/incidents/` на сервере homelab.

## API-ключ Uptime Kuma (опционально)

Для Prometheus `/metrics` (не для webhook):

1. Uptime Kuma → Settings → API Keys
2. Ключ в `agent-web/.env`: `UPTIME_KUMA_API=...`
3. Проверка: `curl -u ":$UPTIME_KUMA_API" http://uptime-kuma:3001/metrics` (из контейнера агента)

## Диагностика

| Проблема | Проверка |
|----------|----------|
| Webhook не доходит | URL с LAN IP, не `localhost` с другой машины |
| Нет анализа в Telegram | `docker logs homelab-agent`, `CURSOR_API_KEY` |
| 404 на VPS | `VPS_WEBHOOK_URL`, деплой `vps-setup/api/uptime-alerts.php` |
| Тест OK, реальный Down — нет | Уведомление привязано к монитору? |

См. также: [INCIDENT_FLOW.md](INCIDENT_FLOW.md), [README.md](README.md)
