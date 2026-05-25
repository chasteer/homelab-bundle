# Настройка GitHub Webhook для автоматического анализа PR

## 🎯 Что это дает

Агент теперь может автоматически:
- ✅ Анализировать код в новых/обновленных Pull Request
- ✅ Проверять критические ошибки (необработанные исключения, синтаксис)
- ✅ Проверять стиль кода (PEP 8, наименования переменных)
- ✅ Добавлять комментарии к PR с найденными проблемами
- ✅ Предлагать исправления

## ⚠️ Важно: Доступ из интернета

Поскольку сервер работает в локальной сети, GitHub не может достучаться до webhook напрямую. Нужно настроить туннелирование.

## 🔧 Настройка

### 0. Настройка туннелирования (выберите один вариант)

#### **Вариант A: ngrok (рекомендуется)**

1. Установите ngrok:
   ```bash
   # Ubuntu/Debian
   sudo apt install ngrok
   
   # Или скачайте с https://ngrok.com/download
   ```

2. Зарегистрируйтесь на https://ngrok.com и получите auth token

3. Настройте ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. Запустите туннель:
   ```bash
   ngrok http your_local_ip:8000
   ```

5. Скопируйте HTTPS URL (например: `https://abc123.ngrok.io`)

#### **Вариант B: Cloudflare Tunnel**

1. Установите cloudflared:
   ```bash
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. Войдите в Cloudflare:
   ```bash
   cloudflared tunnel login
   ```

3. Создайте туннель:
   ```bash
   cloudflared tunnel create homelab-agent
   ```

4. Настройте туннель:
   ```bash
   cloudflared tunnel route dns homelab-agent agent.yourdomain.com
   ```

5. Запустите туннель:
   ```bash
   cloudflared tunnel run homelab-agent
   ```

#### **Вариант C: SSH туннель (если есть VPS)**

1. На VPS создайте SSH туннель:
   ```bash
   ssh -R 8000:your_local_ip:8000 user@your-vps.com
   ```

2. На VPS настройте nginx для проксирования:
   ```nginx
   server {
       listen 80;
       server_name agent.yourdomain.com;
       location / {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### 1. Создание GitHub Personal Access Token

1. Перейдите в GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Нажмите "Generate new token (classic)"
3. Выберите следующие права:
   - `repo` (полный доступ к репозиториям)
   - `public_repo` (если нужен доступ только к публичным репозиториям)
4. Скопируйте токен и сохраните в `.env` как `GITHUB_TOKEN`

### 2. Настройка Webhook в репозитории

1. Перейдите в ваш репозиторий → Settings → Webhooks
2. Нажмите "Add webhook"
3. Заполните:
   - **Payload URL**: `https://YOUR_TUNNEL_URL/webhook/github` (например: `https://abc123.ngrok.io/webhook/github`)
   - **Content type**: `application/json`
   - **Secret**: используйте значение `GITHUB_WEBHOOK_SECRET` из `.env`
   - **Events**: выберите "Pull requests"
4. Нажмите "Add webhook"

### 3. Переменные окружения

Добавьте в `services/.env`:

```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your_secret_here
```

## 🚀 Использование

### Автоматический режим (через webhook)

1. Создайте Pull Request в репозитории
2. Агент автоматически получит уведомление
3. Проанализирует код и добавит комментарий

### Ручной режим

> **Чат-агент удалён.** `POST /api/chat` больше не доступен.

Webhook `POST /webhook/github` только **логирует** события PR в PostgreSQL. Для анализа кода используйте Cursor IDE или расширьте `app.py` под Cursor CLI.

## 🔍 Что анализируется

### Критические ошибки:
- ❌ Необработанные исключения (`except:`)
- ❌ Bare except (`except` без типа)
- ❌ Синтаксические ошибки

### Стиль кода:
- ⚠️ Использование `print()` вместо `logging`
- ⚠️ Слишком длинные строки (>120 символов)
- ⚠️ Неправильные наименования (camelCase вместо snake_case)
- ⚠️ Магические числа без комментариев

### Пример комментария к PR:

```markdown
🤖 **Автоматический анализ кода**

🔍 **Найденные проблемы:**

1. **Критическая ошибка** (строка 15): Необработанное исключение - используйте конкретный тип исключения
   💡 **Рекомендация**: Замените на except SpecificException: или except Exception as e:

2. **Стиль кода** (строка 23): Использование print() в коде
   💡 **Рекомендация**: Используйте logging вместо print()

💡 Рекомендую исправить найденные проблемы перед мержем.
```

## 🛠️ Расширение функциональности

Для добавления новых проверок отредактируйте файл `agent/tools.py`, функцию `_analyze_python_code()`.

## 🔒 Безопасность

- Webhook проверяет подпись для предотвращения подделки запросов
- GitHub токен имеет минимально необходимые права
- Все действия логируются в базу данных агента

## 📝 Логи

Все webhook события логируются в SQLite базу:
- Успешные анализы: `kind="webhook"`
- Ошибки: `kind="webhook_error"`

Просмотреть логи: `GET http://<HOMELAB_HOST>:8000/api/logs?kind=webhook` или `docker compose -f agent-web/docker-compose.yml exec agent-db psql -U agent -d homelab_agent`.

## 🔄 Автоматизация туннелирования

### Автозапуск ngrok с systemd

Создайте сервис для автоматического запуска ngrok:

```bash
sudo nano /etc/systemd/system/ngrok-agent.service
```

Содержимое файла:
```ini
[Unit]
Description=ngrok tunnel for homelab agent
After=network.target

[Service]
Type=simple
User=your_username
ExecStart=/usr/bin/ngrok http your_local_ip:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Включите и запустите сервис:
```bash
sudo systemctl enable ngrok-agent.service
sudo systemctl start ngrok-agent.service
```

### Получение URL туннеля

Для автоматического получения URL туннеля создайте скрипт:

```bash
#!/bin/bash
# get_tunnel_url.sh

# Получаем URL из ngrok API
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

if [ "$TUNNEL_URL" != "null" ] && [ -n "$TUNNEL_URL" ]; then
    echo "🌐 Туннель активен: $TUNNEL_URL"
    echo "🔗 Webhook URL: $TUNNEL_URL/webhook/github"
else
    echo "❌ Туннель не активен"
fi
```

### Альтернатива: Polling вместо Webhook

Если туннелирование не подходит, можно использовать polling:

1. Создайте cron задачу для проверки новых PR:
```bash
# Проверка каждые 5 минут
*/5 * * * * /path/to/check_pr.sh
```

2. Скрипт проверки:
```bash
#!/bin/bash
# check_pr.sh

# Получаем список открытых PR
PR_LIST=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/owner/repo/pulls?state=open" | \
    jq -r '.[] | select(.created_at > "'$(date -d '5 minutes ago' -Iseconds)'") | .number')

for pr in $PR_LIST; do
    # Запускаем анализ
    # Чат-агент удалён; webhook только логирует PR:
    curl -X POST "http://<HOMELAB_HOST>:8000/webhook/github" \
        -H "Content-Type: application/json" \
        -d '{"action":"opened","pull_request":{...},"repository":{...}}'
done
```

## 🛡️ Безопасность туннелирования

- Используйте HTTPS туннели (ngrok, Cloudflare)
- Настройте аутентификацию в webhook
- Ограничьте доступ по IP (если возможно)
- Регулярно обновляйте секреты
- Мониторьте логи на подозрительную активность
