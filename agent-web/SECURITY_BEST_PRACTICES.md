# 🔒 Безопасность и лучшие практики

## 🚨 Важные принципы безопасности

### 1. Никогда не хардкодите чувствительные данные
❌ **Плохо:**
```python
KUMA_URL = "http://your_local_ip:3001"
VPS_URL = "https://your_vps_domain.com/api/uptime-alerts"
```

✅ **Хорошо:**
```python
KUMA_URL = os.environ.get("UPTIME_KUMA_URL", "http://localhost:3001")
VPS_URL = os.environ.get("VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts")
```

### 2. Используйте переменные окружения
Все чувствительные данные должны храниться в файле `.env`:
```bash
# .env
HOMELAB_HOST=your_local_ip_here
UPTIME_KUMA_URL=http://your_local_ip:3001
VPS_WEBHOOK_URL=https://your_vps_domain.com/api/uptime-alerts
GIGACHAT_CREDENTIALS=your_secret_here
```

### 3. Не коммитьте .env файлы
Убедитесь, что `.env` добавлен в `.gitignore`:
```gitignore
.env
*.env
.env.local
```

## 🛡️ Безопасность переменных окружения

### Обязательные переменные
```bash
# API ключи (никогда не оставляйте пустыми)
GIGACHAT_CREDENTIALS=your_real_credentials
TAVILY_API_KEY=your_real_api_key
GITHUB_TOKEN=your_real_token

# Сетевые настройки
HOMELAB_HOST=your_local_ip
UPTIME_KUMA_URL=http://your_ip:3001
VPS_WEBHOOK_URL=https://your_vps.com/api/endpoint
```

### Переменные с значениями по умолчанию
```bash
# Безопасные значения по умолчанию
TZ=${TZ:-UTC}
DEBUG=${DEBUG:-false}
LOG_LEVEL=${LOG_LEVEL:-INFO}
```

## 🔐 Безопасность Docker

### 1. Не используйте root пользователя
```dockerfile
# Хорошо
RUN useradd -m -s /bin/bash agent
USER agent
```

### 2. Ограничивайте доступ к Docker socket
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # Только чтение
```

### 3. Используйте секреты для паролей
```yaml
environment:
  - POSTGRES_PASSWORD=${AGENT_DB_PASSWORD}
```

## 🌐 Сетевая безопасность

### 1. Ограничивайте доступ к портам
```yaml
ports:
  - "${HOMELAB_HOST}:8000:8000"  # Только локальный доступ
```

### 2. Используйте внутренние сети Docker
```yaml
networks:
  - homelab  # Изолированная сеть
```

### 3. Проверяйте входящие соединения
```python
# В коде
if request.client.host not in ALLOWED_HOSTS:
    raise HTTPException(status_code=403, detail="Access denied")
```

## 📝 Проверка безопасности

### Автоматическая проверка
Запустите скрипт для проверки настроек:
```bash
python3 get_system_ip.py
```

### Ручная проверка
1. Убедитесь, что в коде нет жестко закодированных IP
2. Проверьте, что все API ключи в .env
3. Убедитесь, что .env не в git
4. Проверьте права доступа к файлам

## 🚀 Рекомендации по развертыванию

### 1. Разработка
```bash
# Создайте .env.dev для разработки
cp env.example .env.dev
# Заполните тестовыми значениями
```

### 2. Продакшн
```bash
# Создайте .env.prod для продакшна
cp env.example .env.prod
# Заполните реальными значениями
# Никогда не коммитьте .env.prod
```

### 3. CI/CD
```bash
# В CI/CD используйте секреты
- name: Deploy
  env:
    HOMELAB_HOST: ${{ secrets.HOMELAB_HOST }}
    VPS_WEBHOOK_URL: ${{ secrets.VPS_WEBHOOK_URL }}
```

## 🔍 Мониторинг безопасности

### Логирование
```python
import logging

logging.info(f"Webhook received from {request.client.host}")
logging.warning(f"Unauthorized access attempt from {request.client.host}")
```

### Алерты
Настройте уведомления о подозрительной активности:
- Множественные неудачные попытки входа
- Необычные IP адреса
- Большое количество запросов

## 📚 Дополнительные ресурсы

- [OWASP Security Guidelines](https://owasp.org/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## ✅ Чек-лист безопасности

- [ ] Все IP адреса в переменных окружения
- [ ] API ключи не в коде
- [ ] .env файлы в .gitignore
- [ ] Docker контейнеры не root
- [ ] Ограниченный доступ к портам
- [ ] Логирование безопасности
- [ ] Регулярные обновления зависимостей
- [ ] Мониторинг подозрительной активности

Помните: безопасность - это процесс, а не одноразовое действие! 🔒
