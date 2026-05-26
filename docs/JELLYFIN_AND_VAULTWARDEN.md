# Jellyfin и Vaultwarden — кратко

## Vaultwarden: бесконечная загрузка в браузере

### Причина 1: Web Crypto (ошибка в консоли)

```
Could not locate Subtle crypto
```

Веб-хранилище Bitwarden **не работает по HTTP на IP** (`http://192.168.1.200:8081`). Браузер даёт `crypto.subtle` только в **secure context**:

- `https://…`
- или `http://127.0.0.1` / `localhost` на **этой же** машине

Сервер может быть healthy, а UI крутится — это ограничение браузера, не Docker.

### Решение: HTTPS через Caddy

1. Прописать hosts (на ПК, с которого открываете браузер):

```bash
cd /path/to/home_lab
HOMELAB_HOST=192.168.1.200 ./dns/set_local_hosts.sh
# или вручную: 192.168.1.200 vaultwarden.home.arpa
```

2. Запустить прокси:

```bash
./scripts/30_deploy_proxy_caddy.sh
```

3. В `services/.env`:

```env
VW_DOMAIN=https://vaultwarden.home.arpa
```

4. Пересоздать Vaultwarden:

```bash
cd services && docker compose up -d --force-recreate vaultwarden
```

5. Открывать в браузере: **https://vaultwarden.home.arpa** (не `http://192.168.1.200:8081`).

### Расширение Bitwarden в Chrome

Ошибка *«this server was not configured to provide HTTPS»* почти всегда из‑за **неправильного Server URL** в расширении:

| Неправильно | Правильно |
|-------------|-----------|
| `http://192.168.1.200:8081` | `https://vaultwarden.home.arpa` |
| `https://vaultwarden.home.arpa/` (слэш в конце) | без завершающего `/` |

В расширении: **Настройки → Самостоятельный хостинг → URL сервера** — только `https://vaultwarden.home.arpa`. Поля «Custom environment» оставьте пустыми.

Сертификат Caddy должен быть доверен **в Chrome** (Linux: `chrome://certificate-manager` или NSS, не только системный store).

Обновите Vaultwarden (Chrome часто опережает API):

```bash
cd services && docker compose pull vaultwarden && docker compose up -d --force-recreate vaultwarden
```

Проверка API (должен быть JSON, не HTML 404):

```bash
curl -sk -X POST https://vaultwarden.home.arpa/identity/accounts/prelogin \
  -H 'Content-Type: application/json' -d '{"email":"you@example.com"}'
```

### «Подключение не защищено» — это нормально для `tls internal`

Caddy шифрует трафик **своим локальным CA**. Для браузера это не публичный Let's Encrypt, пока вы не доверите корню.

**Вариант A — доверить CA на своих устройствах (рекомендуется для LAN):**

```bash
./scripts/export_caddy_root_ca.sh ~/caddy-homelab-root.crt
```

Импортируйте `caddy-homelab-root.crt` в «Доверенные корневые центры» (Windows/Firefox/macOS/Linux — подсказки в выводе скрипта). Перезапустите браузер → замок без предупреждения на `https://vaultwarden.home.arpa`.

**Вариант B — настоящий Let's Encrypt (для доступа из интернета):**

В `services/.env`:

```env
VW_PUBLIC_DOMAIN=vault.babeshin.ru
ACME_EMAIL=you@example.com
VW_DOMAIN=https://vault.babeshin.ru
```

DNS: `A` запись на белый IP homelab. Роутер: проброс **80** и **443** на `HOMELAB_HOST`. Затем:

```bash
./scripts/30_deploy_proxy_caddy.sh
cd services && docker compose up -d --force-recreate vaultwarden
```

Открывать `https://vault.babeshin.ru` (без hosts). Сертификат будет от Let's Encrypt.

`.home.arpa` **нельзя** получить в публичном CA — только локальный CA или отдельный публичный домен.

### Временный обход без HTTPS

SSH-туннель на машине с браузером:

```bash
ssh -L 8081:127.0.0.1:8081 user@192.168.1.200
```

Затем **http://127.0.0.1:8081** и `VW_DOMAIN=http://127.0.0.1:8081` (только для этого сценария).

### Диагностика

```bash
docker compose ps vaultwarden
docker compose logs vaultwarden --tail 50
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.1.200:8081/
curl -sS http://192.168.1.200:8081/alive
```

Права на данные:

```bash
sudo chown -R 1000:1000 /srv/secrets/vaultwarden
```

### Healthcheck в Docker

В образе Vaultwarden **нет `wget`** — старый healthcheck давал `unhealthy`, хотя сервис работал. В compose используется `curl http://127.0.0.1/alive`.

Статус **(health: starting)** — подождите ~20 с после старта.

---

## Jellyfin: как пользоваться в этом homelab

### Откуда контент

Jellyfin **не раздаёт** фильмы и сериалы — только показывает то, что лежит на диске.

В этом проекте библиотека смонтирована так:

| Путь в контейнере | На хосте |
|-------------------|----------|
| `/media` | `/srv/media/library` |

**Легально:** свои файлы, DVD/Blu-ray рипы, покупки, подписки, которые вы сами положили в библиотеку.

**Типичная схема homelab (у вас есть TorrServer):**

1. TorrServer — `http://<HOMELAB_HOST>:8090` — торрент-стриминг в браузере.
2. Файлы для Jellyfin — копировать/скачивать в `/srv/media/library` (фильмы, сериалы — отдельные папки).
3. Плагины Jellyfin (например **TorrServer**, **Jellyscrub**) — настраиваются в веб-UI Jellyfin; источники торрентов/трекеров — ваша ответственность и местное законодательство.

Структура библиотеки (пример):

```text
/srv/media/library/
  Movies/
    Название фильма (2024)/
      movie.mkv
  Shows/
    Название сериала/
      Season 01/
        S01E01.mkv
```

В Jellyfin: **Панель управления → Библиотеки → Добавить** — тип «Фильмы» / «Сериалы», папки `/media/Movies`, `/media/Shows`.

### Адреса

| Способ | URL |
|--------|-----|
| По IP | `http://192.168.1.200:8096` |
| По имени (после `set_local_hosts.sh`) | `http://jellyfin.home.arpa:8096` |
| Через Caddy/Traefik | `http://jellyfin.home.arpa` (если включён `proxy/`) |

Первый запуск: мастер, создать пользователя, добавить библиотеки, **Scan library**.

### Перезапуск и плагины

Плагины ставятся в UI; **после установки или обновления плагина нужен перезапуск Jellyfin**:

```bash
cd services
docker compose restart jellyfin
# или полное пересоздание при смене образа:
docker compose pull jellyfin
docker compose up -d jellyfin
```

Проверка:

```bash
docker compose ps jellyfin
docker compose logs jellyfin --tail 30
curl -sS http://192.168.1.200:8096/health
```

Конфиг и плагины на диске: `/srv/media/config/jellyfin` (сохраняется между перезапусками).

### Обновление метаданных

- **Dashboard → Scheduled Tasks** — сканирование библиотек.
- Или вручную: библиотека → **Scan library**.

После копирования новых файлов в `/srv/media/library` — scan или дождаться расписания.

### Связка с TorrServer

1. Запустить оба: `docker compose up -d jellyfin torrserver`
2. В Jellyfin: **Dashboard → Plugins → Catalog** — найти плагин под TorrServer (если используете).
3. В настройках плагина указать URL TorrServer: `http://torrserver:8090` (из контейнера Jellyfin) или `http://192.168.1.200:8090` (с хоста).

Имена контейнеров в одной сети `homelab` видят друг друга по имени (`torrserver`, `jellyfin`).

### Остановка для тестов (Uptime Kuma)

```bash
cd services
docker compose stop jellyfin    # тест «сервис упал»
docker compose start jellyfin   # поднять снова
```

Не останавливайте `uptime-kuma` и `homelab-agent`, если проверяете алерты.
