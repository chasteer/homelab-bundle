# Homelab Bundle

Домашний сервер на Docker: медиа, фото, пароли, мониторинг и **автоматический разбор инцидентов** с уведомлениями в Telegram.

## Возможности

| Область | Сервисы |
|---------|---------|
| Медиа | Jellyfin, TorrServer |
| Фото | Immich (+ PostgreSQL, Redis, ML) |
| Пароли | Vaultwarden |
| Мониторинг | Uptime Kuma |
| Инциденты | **Homelab Incident Service** — Uptime Kuma → Cursor CLI → VPS → Telegram |
| Прокси (опц.) | Caddy / Traefik |
| Внешний доступ (опц.) | ngrok, SSH-туннель |

Чат-бот и LangGraph **удалены**. Агент (`agent-web`) — это webhook-сервис, не веб-чат.

## Архитектура инцидентов

```
Uptime Kuma (падение сервиса)
    → POST /api/webhook/uptime-kuma  (homelab-agent:8000)
    → Cursor CLI (agent -p, анализ репозитория homelab)
    → logs/incidents/*.md (полный отчёт)
    → POST VPS /api/uptime-alerts
    → Telegram (краткий текст, ≤1400 символов)
```

Подробнее: [agent-web/INCIDENT_FLOW.md](agent-web/INCIDENT_FLOW.md)

## Быстрый старт

### Требования

- Ubuntu 22.04+ (или аналог)
- Docker и Docker Compose
- Пользователь в группе `docker`
- 4 GB+ RAM, 50 GB+ диск

### Установка

```bash
git clone <your-repo-url> home_lab
cd home_lab
./scripts/deploy_all.sh
```

Или по шагам:

```bash
./scripts/20_deploy_core.sh          # services/ — Jellyfin, Immich, Uptime Kuma, …
./scripts/40_deploy_agent_web.sh     # agent-web — incident service
```

### Сеть Docker

Все сервисы в **внешней** сети `homelab`:

```bash
docker network create homelab   # если ещё нет
```

## Порты (типичные)

| Сервис | Порт | Примечание |
|--------|------|------------|
| Jellyfin | 8096 | привязка к `HOMELAB_HOST` |
| TorrServer | 8090 | |
| Immich | 2283 | |
| Vaultwarden | 8081 | |
| Uptime Kuma | 3001 | |
| Homelab Agent | 8000 | webhook API, не чат-UI |

Порты задаются в `services/.env` и `agent-web/.env` через `HOMELAB_HOST` (LAN IP сервера).

## Конфигурация

### `services/.env`

```env
HOMELAB_HOST=192.168.1.200
TZ=Europe/Moscow
IMMICH_DB_PASSWORD=...
```

### `agent-web/.env`

```env
HOMELAB_HOST=192.168.1.200
CURSOR_API_KEY=...                    # https://cursor.com/dashboard
VPS_WEBHOOK_URL=https://your-vps/api/uptime-alerts
UPTIME_KUMA_URL=http://uptime-kuma:3001
UPTIME_KUMA_API=...                   # Prometheus API key, /metrics
AGENT_WEBHOOK_URL=http://192.168.1.200:8000/api/webhook/uptime-kuma
```

Шаблон: [agent-web/env.example](agent-web/env.example)

## Управление

```bash
./scripts/check_status.sh
./scripts/agent_manage.sh status
./scripts/agent_manage.sh logs

cd services && docker compose ps
cd agent-web && docker compose ps
```

Проверка Cursor CLI в агенте:

```bash
cd agent-web
bash scripts/test_cursor_in_container.sh
```

## Документация

| Документ | Описание |
|----------|----------|
| [agent-web/README.md](agent-web/README.md) | Incident Service, API, Docker |
| [agent-web/INCIDENT_FLOW.md](agent-web/INCIDENT_FLOW.md) | Cursor CLI, переменные, тесты |
| [agent-web/uptime_kuma_webhook_setup.md](agent-web/uptime_kuma_webhook_setup.md) | Webhook в Uptime Kuma |
| [vps-setup/README.md](vps-setup/README.md) | VPS → Telegram |
| [vps-setup/TELEGRAM_SETUP.md](vps-setup/TELEGRAM_SETUP.md) | Настройка бота |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Типичные ошибки |
| [docs/JELLYFIN_AND_VAULTWARDEN.md](docs/JELLYFIN_AND_VAULTWARDEN.md) | Jellyfin, Vaultwarden |
| [SECURITY.md](SECURITY.md) | Секреты, `.gitignore`, что не коммитить |
| [GITHUB_WEBHOOK_SETUP.md](GITHUB_WEBHOOK_SETUP.md) | GitHub (опционально) |

Устаревшие (чат/LLM): см. пометки в `agent-web/GROQ_SETUP.md`, `LLM_SWITCHING_GUIDE.md`.

## Лицензия

MIT — см. [LICENSE](LICENSE).
