# Безопасность и секреты

## Что не должно попадать в Git

| Файл / данные | Где хранить |
|---------------|-------------|
| `CURSOR_API_KEY`, `UPTIME_KUMA_API`, `GITHUB_TOKEN` | `agent-web/.env` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `vps-setup/.env` |
| `IMMICH_DB_PASSWORD`, `HOMELAB_HOST` | `services/.env` |
| Отчёты инцидентов | `agent-web/logs/incidents/` (в `.gitignore`) |
| `github-config/polling.conf` | локально, в `.gitignore` |

Шаблоны без реальных значений: `env.example`, `agent-web/env.example`, `vps-setup/env.example`.

## Проверка перед коммитом

```bash
# Нет .env в индексе
git ls-files | grep -E '\.env$' && echo "ОШИБКА: .env в git" || echo "OK: .env не tracked"

# Поиск похожих на ключи в staged
git diff --cached | grep -iE 'ghp_|sk-|api_key.*=[a-zA-Z0-9]{20,}' || true

# Секреты в истории (опционально)
# pip install detect-secrets && detect-secrets scan
```

## Если секрет уже попал в Git

1. Смените ключ / пароль в сервисе (Cursor, Telegram, GitHub, Uptime Kuma).
2. Удалите файл из истории (`git filter-repo` / BFG) или считайте ключ скомпрометированным.
3. Не коммитьте `.idea/` — там могут быть SSH/host (см. `.gitignore`).

## Слабые значения по умолчанию

В репозитории **нет** реальных API-ключей. Допустимы только плейсхолдеры в документации и `env.example`.

Пароль БД задаётся только через `AGENT_DB_PASSWORD` в `.env` (не хардкод в `app.py`).

## Логи

`webhook_uptime.py` пишет в stdout заголовки webhook — не логируйте production с `DEBUG` на публичных логах. Полные отчёты — в `logs/incidents/`.
