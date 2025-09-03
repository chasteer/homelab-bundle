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

### Логи
```bash
sudo docker compose -f services/docker-compose.yml logs
sudo docker compose -f agent-web/docker-compose.yml logs
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
