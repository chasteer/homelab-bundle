# Homelab stack (актуальная схема)

## Сервисы

| Сервис | URL (HTTPS) | Прямой порт |
|--------|-------------|-------------|
| Jellyfin | https://jellyfin.home.arpa | :8096 |
| TorrServer | https://torrserver.home.arpa | :8090 |
| Immich | https://immich.home.arpa | :2283 |
| Vaultwarden | https://vaultwarden.home.arpa | :8081 (мобильные клиенты) |
| Uptime Kuma | https://kuma.home.arpa | :3001 |
| Homelab Agent | https://agent.home.arpa | :8000 |
| it-tools | https://it-tools.home.arpa | — |
| Dozzle | https://dozzle.home.arpa | — |
| Home Assistant | https://homeassistant.home.arpa | — |

DNS: `HOMELAB_HOST` + `*.home.arpa` (роутер или `./dns/set_local_hosts.sh`).

## Caddy (HTTPS)

Все веб-UI доступны по HTTPS через Caddy **без отдельного SSO** — только TLS и reverse proxy.

```bash
./scripts/30_deploy_proxy_caddy.sh
```

Импорт CA Caddy (зелёный замок в LAN): `./scripts/export_caddy_root_ca.sh`

## Инциденты и логи

При падении монитора агент:

1. Сопоставляет имя монитора → контейнер (`agent/container_logs.py`)
2. Выполняет `docker logs <container> --tail 150`
3. Передаёт логи в Cursor CLI → краткий отчёт в Telegram

Переменные (`agent-web/.env`):

```env
CONTAINER_LOG_TAIL=150
CONTAINER_LOG_MAX_CHARS=12000
```

Ручной просмотр логов: https://dozzle.home.arpa

## Home Assistant

Первый запуск: https://homeassistant.home.arpa → мастер настройки. Конфиг: `/srv/homeassistant`.

Для Zigbee/Z-Wave позже может понадобиться `devices:` в compose — см. документацию HA.

## Развёртывание

```bash
./scripts/10_prepare_dirs.sh
./scripts/20_deploy_core.sh
./scripts/30_deploy_proxy_caddy.sh
./scripts/40_deploy_agent_web.sh
```
