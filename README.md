# 🏠 Homelab Bundle - Полнофункциональный домашний сервер

Полнофункциональный набор сервисов для домашнего сервера с автоматическим развертыванием, мониторингом и управлением через веб-интерфейс.

## 🌟 Особенности

- **🎬 Медиа-сервисы**: Jellyfin, TorrServer
- **📸 Фото-сервисы**: Immich с машинным обучением
- **🔐 Безопасность**: Vaultwarden (Bitwarden)
- **📊 Мониторинг**: Uptime Kuma
- **🤖 Управление**: Homelab Agent с веб-интерфейсом
- **🌐 Прокси**: Caddy/Traefik с HTTPS
- **🔒 Безопасность**: UFW firewall
- **📱 Внешний доступ**: ngrok/SSH туннели

## 🚀 Быстрый старт

### Требования
- Ubuntu 22.04+ или совместимый дистрибутив
- Docker и Docker Compose
- Минимум 4GB RAM, 50GB свободного места

### Установка
```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/homelab-bundle.git
cd homelab-bundle

# Запустите автоматическое развертывание
./scripts/deploy_all.sh
```

### Автоматическое развертывание
Скрипт `deploy_all.sh` автоматически выполнит:
1. ✅ Подготовку системы
2. 📁 Создание директорий
3. ⚙️ Настройку переменных окружения
4. 🐳 Развертывание основных сервисов
5. 🤖 Развертывание Homelab Agent
6. 🔒 Настройку UFW firewall
7. 🌐 Настройку прокси (опционально)
8. 🌍 Настройку внешнего доступа (опционально)

## 📋 Доступные сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| 🌐 Jellyfin | 8096 | Медиа-сервер |
| 📥 TorrServer | 8090 | Торрент-сервер |
| 📸 Immich | 2283 | Фото-сервис с ML |
| 🔐 Vaultwarden | 8081 | Менеджер паролей |
| 📊 Uptime Kuma | 3001 | Мониторинг сервисов |
| 🤖 Homelab Agent | 8000 | Веб-интерфейс управления |

## 🛠️ Управление

### Основные команды
```bash
# Статус всех сервисов
./scripts/check_status.sh

# Управление агентом
./scripts/agent_manage.sh status
./scripts/agent_manage.sh logs
./scripts/agent_manage.sh restart

# Очистка Docker ресурсов
./scripts/cleanup_docker.sh
```

### Docker Compose команды
```bash
# Статус сервисов
sudo docker compose -f services/docker-compose.yml ps

# Статус агента
sudo docker compose -f agent-web/docker-compose.yml ps

# Логи сервисов
sudo docker compose -f services/docker-compose.yml logs -f
```

## 🔧 Конфигурация

### Переменные окружения
Создайте файл `services/.env` на основе `services/.env.example`:
```bash
# Основные настройки
TZ=Europe/Moscow
DOMAIN=your-domain.com

# API ключи
GIGACHAT_CREDENTIALS=your_gigachat_credentials
TAVILY_API_KEY=your_tavily_api_key
GITHUB_TOKEN=your_github_token
```

### Настройка сети
Все сервисы работают в сети Docker `homelab` с IP `192.168.1.200`.

## 🔒 Безопасность

- **Firewall**: UFW с предустановленными правилами
- **Изоляция**: Каждый сервис в отдельном контейнере
- **Сеть**: Изолированная Docker сеть
- **Прокси**: HTTPS с Let's Encrypt (опционально)

## 📚 Документация

- [📖 Руководство по развертыванию](DEPLOYMENT_GUIDE.md)
- [🔧 Устранение неполадок](TROUBLESHOOTING.md)
- [🌐 Интеграция с GitHub](GITHUB_INTEGRATION_GUIDE.md)
- [🔒 Анализ безопасности](SECURITY_ANALYSIS.md)
- [🚫 Блокировка сервисов](BLOCKED_SERVICES_GUIDE.md)

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- 📖 [Документация](docs/)
- 🐛 [Issues](https://github.com/yourusername/homelab-bundle/issues)
- 💬 [Discussions](https://github.com/yourusername/homelab-bundle/discussions)

## ⭐ Звезды

Если проект вам понравился, поставьте звезду! ⭐

---

**Создано с ❤️ для домашних серверов**
