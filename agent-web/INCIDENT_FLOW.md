# Обработка падений (Uptime Kuma + Cursor CLI)

## Поток

1. **Uptime Kuma** → `POST /api/webhook/uptime-kuma`
2. При статусе **down/error** → **`docker logs`** проблемного контейнера (`agent/container_logs.py`)
3. → **`agent -p --trust --mode ask`** (логи + репозиторий `/app/homelab`)
4. **Полный отчёт** → `logs/incidents/*.md` на сервере
5. **Краткий текст** (≤ `CURSOR_TELEGRAM_MAX_CHARS`) → **VPS** → **Telegram**

Переменные: `CONTAINER_LOG_TAIL` (по умолчанию 150), `CONTAINER_LOG_MAX_CHARS`. Ручной просмотр логов: https://dozzle.home.arpa

## Формат ответа Cursor (для Telegram)

Агент требует от CLI только 4 блока:

- **Причина** (1–2 предложения)
- **Проверить** (до 3 команд)
- **Исправить** (до 4 шагов)
- **Серьёзность** (low / medium / high / critical)

Без вступлений («ищу в репозитории…»). При превышении лимита текст обрезается с пометкой и путём к полному отчёту.

## Cursor CLI в Docker

При сборке образа:

```bash
curl https://cursor.com/install -fsS | bash
```

Бинарник: `/home/agent/.local/bin/agent`

### Обязательно в `agent-web/.env`

```env
CURSOR_API_KEY=...          # https://cursor.com/dashboard
HOMELAB_HOST=192.168.1.200  # для привязки порта 8000
VPS_WEBHOOK_URL=https://...
```

### Пересборка и запуск

```bash
cd agent-web
docker compose build --no-cache agent
docker compose up -d agent
```

### Проверка

```bash
bash scripts/test_cursor_in_container.sh
```

Или вручную:

```bash
curl -s http://<HOMELAB_HOST>:8000/api/health | python3 -m json.tool
docker compose exec agent /home/agent/.local/bin/agent --version
curl -X POST http://<HOMELAB_HOST>:8000/api/webhook/uptime-kuma/test-cursor
```

## Переменные

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `CURSOR_API_KEY` | — | API-ключ Cursor (обязателен) |
| `CURSOR_CLI_PATH` | `/home/agent/.local/bin/agent` | Путь к CLI |
| `CURSOR_WORKSPACE` | `/app/homelab` | Монтированный репозиторий |
| `CURSOR_AGENT_MODE` | `ask` | `ask` / `plan` |
| `CURSOR_OUTPUT_FORMAT` | `json` | Рекомендуется в Docker |
| `CURSOR_TELEGRAM_MAX_CHARS` | `1400` | Лимит текста в Telegram |
| `CURSOR_CLI_TIMEOUT` | `300` | Таймаут subprocess (сек) |
| `CURSOR_INCIDENT_ENABLED` | `true` | Включить CLI |
| `CURSOR_INCIDENT_REQUIRED` | `true` | Не подменять шаблоном при ошибке |
| `VPS_WEBHOOK_URL` | — | URL VPS `api/uptime-alerts` |

## Запуск на хосте (без Docker)

```bash
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
export CURSOR_API_KEY=...
export CURSOR_WORKSPACE=/path/to/home_lab
cd agent-web && uvicorn app:app --host 0.0.0.0 --port 8000
```

## Связанные документы

- [README.md](README.md) — обзор сервиса
- [uptime_kuma_webhook_setup.md](uptime_kuma_webhook_setup.md) — настройка в UI Uptime Kuma
- [../vps-setup/README.md](../vps-setup/README.md) — Telegram
