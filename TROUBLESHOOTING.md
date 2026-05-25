# Устранение неполадок Homelab

## Проблема: "Error response from daemon: network with name homelab already exists"

### Причина
Эта ошибка возникает, когда Docker Compose пытается создать сеть `homelab`, которая уже существует, или когда есть конфликт между внешней сетью и автоматически созданной сетью.

### Решение

#### Вариант 1: Автоматическое исправление (рекомендуется)
Запустите скрипт очистки:
```bash
./scripts/cleanup_docker.sh
```

#### Вариант 2: Ручное исправление
1. Остановите все сервисы:
```bash
sudo docker compose -f services/docker-compose.yml down
sudo docker compose -f agent-web/docker-compose.yml down
```

2. Проверьте существующие сети:
```bash
sudo docker network ls | grep homelab
```

3. Удалите лишние сети (оставьте только `homelab`):
```bash
sudo docker network rm homelab_homelab  # если есть
```

4. Запустите заново:
```bash
./scripts/deploy_all.sh
```

### Профилактика
- Всегда используйте `sudo` для Docker команд
- Сеть `homelab` объявлена как `external: true` в docker-compose.yml
- Скрипт `20_deploy_core.sh` автоматически создает сеть перед запуском сервисов

## Другие распространенные проблемы

### Проблема: Permission denied при работе с Docker
**Решение:** Используйте `sudo` перед Docker командами или добавьте пользователя в группу docker:
```bash
sudo usermod -aG docker $USER
# Перезайдите в систему
```

### Проблема: Порт уже используется
**Решение:** Проверьте, какой процесс использует порт:
```bash
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000
```

### Проблема: Недостаточно места на диске
**Решение:** Очистите Docker:
```bash
sudo docker system prune -a
sudo docker volume prune
```

## Полезные команды

### Проверка статуса
```bash
./scripts/check_status.sh          # Общий статус
./scripts/agent_manage.sh status   # Статус агента
sudo docker compose -f services/docker-compose.yml ps
```

### Homelab Agent: Cursor CLI / webhook

**Симптом:** `permission denied` при `docker compose`
```bash
sudo usermod -aG docker $USER
newgrp docker   # или перелогин
```

**Симптом:** `curl localhost:8000` — connection refused  
Порт привязан к `HOMELAB_HOST` из `.env`, не к 127.0.0.1:
```bash
curl -s http://$(grep HOMELAB_HOST agent-web/.env | cut -d= -f2):8000/api/health
```

**Симптом:** `Cursor CLI вернул пустой ответ`
1. Проверьте `CURSOR_API_KEY` в `agent-web/.env`
2. Пересоберите: `cd agent-web && docker compose build --no-cache agent && docker compose up -d agent`
3. Тест: `bash agent-web/scripts/test_cursor_in_container.sh`
4. Убедитесь `CURSOR_OUTPUT_FORMAT=json` в docker-compose

**Симптом:** Uptime Kuma webhook не срабатывает  
- Оба контейнера в сети `homelab`: `docker network inspect homelab`
- URL в Uptime Kuma: `http://<LAN-IP>:8000/api/webhook/uptime-kuma`
- Логи: `docker compose -f agent-web/docker-compose.yml logs -f agent`

**Симптом:** Нет сообщения в Telegram  
- `VPS_WEBHOOK_URL` в `agent-web/.env`
- Логи VPS: `tail -f vps-setup/logs/homelab-vps.log` (на VPS)
- См. [vps-setup/README.md](vps-setup/README.md)

### Логи
```bash
docker compose -f services/docker-compose.yml logs
docker compose -f agent-web/docker-compose.yml logs
```

### Перезапуск
```bash
./scripts/agent_manage.sh restart  # Перезапуск агента
sudo docker compose -f services/docker-compose.yml restart
```

## Полная переустановка
Если ничего не помогает:
```bash
./scripts/cleanup_docker.sh
./scripts/deploy_all.sh
```
