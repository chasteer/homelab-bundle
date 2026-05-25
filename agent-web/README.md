# Homelab Incident Service

Webhook-сервис для homelab: при падении монитора **Uptime Kuma** запускается **Cursor CLI**, краткий анализ уходит в **Telegram** через VPS. Полный отчёт сохраняется на диске агента.

> **Не чат.** Эндпоинт `/api/chat` и веб-UI удалены.

## Поток данных

```
Uptime Kuma
  → POST /api/webhook/uptime-kuma
  → agent/cursor_incident.py  (subprocess: agent -p --trust)
  → logs/incidents/YYYYMMDD_HHMMSS_<monitor>_down.md
  → POST VPS_WEBHOOK_URL
  → Telegram
```

## Быстрый старт

### 1. Core-сервисы и сеть

```bash
cd /path/to/home_lab
./scripts/20_deploy_core.sh
docker network ls | grep homelab
```

### 2. Переменные окружения

```bash
cd agent-web
cp env.example .env
nano .env
```

Обязательно:

```env
HOMELAB_HOST=192.168.1.200
CURSOR_API_KEY=your_key_from_cursor_dashboard
VPS_WEBHOOK_URL=https://your-vps.example.com/api/uptime-alerts
UPTIME_KUMA_API=your_uptime_kuma_prometheus_key
```

### 3. Сборка и запуск

```bash
docker compose up -d --build
```

Пользователь должен быть в группе `docker` (`sudo usermod -aG docker $USER`).

### 4. Проверка

```bash
# health (используйте HOMELAB_HOST, не localhost, если порт так привязан)
curl -s http://192.168.1.200:8000/api/health | python3 -m json.tool

bash scripts/test_cursor_in_container.sh
```

## API

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/` | Список эндпоинтов |
| GET | `/api/health` | DB + Cursor CLI + API key |
| POST | `/api/webhook/uptime-kuma` | Алерт от Uptime Kuma |
| POST | `/api/webhook/uptime-kuma/test-cursor` | Тест анализа |
| GET | `/api/webhook/uptime-kuma/health` | Health webhook |
| GET | `/api/logs` | Логи PostgreSQL |
| GET | `/api/services` | `docker ps` из контейнера |
| POST | `/webhook/github` | Логирование PR (без LLM-анализа) |

## Cursor CLI

- Устанавливается в образ: `curl https://cursor.com/install -fsS | bash`
- Бинарник: `/home/agent/.local/bin/agent`
- Репозиторий homelab: `/app/homelab` (volume `..:/app/homelab`)
- Режим по умолчанию: `ask` (краткий ответ)
- Формат вывода: `json` (парсинг поля `result`)

Детали: [INCIDENT_FLOW.md](INCIDENT_FLOW.md)

### Переменные Cursor

| Переменная | По умолчанию |
|------------|--------------|
| `CURSOR_API_KEY` | — (обязательно) |
| `CURSOR_CLI_PATH` | `/home/agent/.local/bin/agent` |
| `CURSOR_WORKSPACE` | `/app/homelab` |
| `CURSOR_AGENT_MODE` | `ask` |
| `CURSOR_OUTPUT_FORMAT` | `json` |
| `CURSOR_TELEGRAM_MAX_CHARS` | `1400` |
| `CURSOR_CLI_TIMEOUT` | `300` |
| `CURSOR_INCIDENT_REQUIRED` | `true` |

## Uptime Kuma

- API-ключ: только endpoint **`/metrics`** (см. [wiki API Keys](https://github.com/louislam/uptime-kuma/wiki/API-Keys))
- Webhook в UI: `http://<HOMELAB_HOST>:8000/api/webhook/uptime-kuma`
- Настройка UI: [uptime_kuma_webhook_setup.md](uptime_kuma_webhook_setup.md)

Socket.IO / веб-логин в агенте **не используются**.

## Контейнеры

| Сервис | Имя | Описание |
|--------|-----|----------|
| agent | homelab-agent | FastAPI + Cursor CLI |
| agent-db | homelab-agent-db | PostgreSQL |
| github-polling | homelab-github-polling | Опционально (`--profile polling`) |

## Команды

```bash
docker compose ps
docker compose logs -f agent
docker compose restart agent
docker compose exec agent /home/agent/.local/bin/agent --version
```

## Устранение неполадок

| Симптом | Решение |
|---------|---------|
| `permission denied` docker.sock | `sudo usermod -aG docker $USER`, `newgrp docker` |
| `curl localhost:8000` не работает | Используйте `HOMELAB_HOST` из `.env` |
| Пустой ответ Cursor CLI | `CURSOR_API_KEY`, пересборка образа, `CURSOR_OUTPUT_FORMAT=json` |
| Нет Telegram | Проверьте `VPS_WEBHOOK_URL`, логи VPS, [vps-setup/README.md](../vps-setup/README.md) |
| Uptime Kuma не достучался | Оба контейнера в сети `homelab`, URL с IP хоста |

Скрипт диагностики: `bash scripts/test_cursor_in_container.sh`

Общие проблемы homelab: [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

## Устаревшая документация

Следующие файлы относятся к **удалённому** чат-агенту (GigaChat/Groq/LangGraph):

- `GROQ_SETUP.md`, `LLM_SWITCHING_GUIDE.md`, `LLM_INCIDENT_ANALYSIS.md`, `PROXY_SETUP.md`

Актуальный анализ инцидентов — только **Cursor CLI** ([INCIDENT_FLOW.md](INCIDENT_FLOW.md)).

## Лицензия

MIT
