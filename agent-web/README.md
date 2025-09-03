# 🤖 Homelab Agent

Интеллектуальный агент для домашнего сервера на основе LangGraph и GigaChat с интеграцией GitHub, поиском в интернете и мониторингом сервисов. **Полностью контейнеризирован** для работы в Docker.

## ✨ Возможности

- **💬 Чат с ИИ** - общение с агентом на естественном языке
- **🔍 Поиск в интернете** - интеграция с Tavily для получения актуальной информации
- **🐙 GitHub интеграция** - автоматический анализ PR/MR, поиск репозиториев
- **📊 Мониторинг сервисов** - проверка состояния Docker контейнеров, портов, ресурсов
- **📚 RAG система** - контекстный поиск по загруженным документам и логам
- **📋 Логирование** - сохранение всех запросов и ответов в PostgreSQL
- **🌐 Веб-интерфейс** - удобный UI для взаимодействия с агентом
- **🐳 Docker контейнеры** - полная контейнеризация с доступом к Docker socket

## 🚀 Быстрый старт

### 1. Подготовка окружения

Убедитесь, что у вас запущены основные сервисы homelab:

```bash
# Запуск основных сервисов
./scripts/20_deploy_core.sh

# Проверка сети homelab
docker network ls | grep homelab
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cd agent-web
cp .env.example .env
```

Заполните необходимые переменные:

```env
# GigaChat API
GIGACHAT_CREDENTIALS=your_gigachat_credentials_here

# Tavily Search API
TAVILY_API_KEY=your_tavily_api_key_here

# GitHub API
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# База данных агента
AGENT_DB_PASSWORD=agent123

# Настройки GitHub polling
POLLING_INTERVAL=300
```

### 3. Запуск агента

```bash
# Автоматическое развертывание
./scripts/40_deploy_agent_web.sh

# Или вручную
docker compose up -d --build
```

Агент будет доступен по адресу: http://your_local_ip:8000

## 🔧 Управление агентом

### Основные команды

```bash
# Статус
./scripts/agent_manage.sh status

# Логи
./scripts/agent_manage.sh logs

# Перезапуск
./scripts/agent_manage.sh restart

# Обновление
./scripts/agent_manage.sh update

# Проверка здоровья
./scripts/agent_manage.sh health

# Статус всех сервисов
./scripts/agent_manage.sh services
```

### Docker Compose команды

```bash
# Статус сервисов
docker compose ps

# Логи агента
docker compose logs -f agent

# Логи базы данных
docker compose logs -f agent-db

# Перезапуск
docker compose restart

# Остановка
docker compose down
```

## 🔧 Настройка GitHub Polling

### Автоматическая проверка PR/MR

GitHub polling работает как отдельный контейнер:

```bash
# Запуск GitHub polling
docker compose --profile polling up -d github-polling

# Проверка статуса
docker compose --profile polling ps github-polling

# Логи
docker compose --profile polling logs -f github-polling
```

### Конфигурация репозиториев

Редактируйте файл `github-config/polling.conf`:

```bash
# Вход в контейнер для редактирования
docker compose exec github-polling bash

# Или редактируйте локально (файл монтируется)
nano github-config/polling.conf
```

Формат конфигурации:
```
owner/repo:branch:webhook_url:secret
```

## 🛠️ Использование

### Веб-интерфейс

1. Откройте http://your_local_ip:8000
2. Загрузите файлы для RAG (логи, compose файлы, документация)
3. Задавайте вопросы агенту на естественном языке
4. Мониторьте статус всех сервисов homelab

### Примеры запросов

```
- Проверь состояние сервисов
- Объясни логи qbittorrent
- Найди информацию о Docker Compose best practices
- Анализ кода owner/repo pr_number
- Сгенерируй docker-compose для nginx
- Мониторинг использования диска
- Статус сети homelab
```

### API endpoints

- `POST /api/chat` - отправка сообщения агенту
- `POST /api/upload` - загрузка файлов для RAG
- `GET /api/logs` - получение логов
- `GET /api/health` - проверка здоровья сервиса
- `GET /api/services` - статус всех сервисов homelab
- `POST /webhook/github` - GitHub webhook для анализа PR

## 🏗️ Архитектура

### Компоненты

- **`app.py`** - FastAPI приложение с веб-интерфейсом
- **`agent/graph.py`** - LangGraph граф агента
- **`agent/llm.py`** - интеграция с GigaChat
- **`agent/tools.py`** - набор инструментов агента
- **`agent/rag.py`** - RAG система для контекстного поиска
- **`github_polling.py`** - GitHub polling сервис

### Контейнеры

- **`agent`** - основной контейнер агента
- **`agent-db`** - PostgreSQL база данных
- **`github-polling`** - GitHub polling сервис (опционально)

### Инструменты агента

- `monitor_homelab_services` - мониторинг состояния сервисов
- `docker_compose_lint` - анализ Docker Compose файлов
- `port_conflict_scan` - проверка конфликтов портов
- `github_search` - поиск в GitHub
- `analyze_code_quality` - анализ качества кода
- `tavily_search` - поиск в интернете
- `get_system_info` - системная информация

## 📊 Мониторинг

### Проверка состояния

```bash
# Статус Docker контейнеров
docker compose ps

# Проверка портов
netstat -tlnp | grep -E ':(8080|2283|8081|3001|8096|8000)'

# Логи агента
docker compose logs -f agent

# Статус GitHub polling
docker compose --profile polling logs -f github-polling
```

### Логи и отладка

- **Логи агента**: `docker compose logs -f agent`
- **Логи базы данных**: `docker compose logs -f agent-db`
- **Логи GitHub polling**: `docker compose --profile polling logs -f github-polling`
- **База данных**: PostgreSQL в контейнере `agent-db`
- **RAG индекс**: `/app/data/index` в контейнере

## 🔒 Безопасность

- **Docker socket** монтируется в режиме read-only
- **Переменные окружения** для чувствительных данных
- **Локальный доступ** по умолчанию (your_local_ip)
- **PostgreSQL** с отдельным пользователем
- **GitHub webhook** подписывается секретным ключом

## 🚨 Устранение неполадок

### Частые проблемы

1. **GigaChat не отвечает**
   - Проверьте `GIGACHAT_CREDENTIALS` в `.env`
   - Убедитесь в доступности API

2. **GitHub polling не работает**
   - Проверьте `GITHUB_TOKEN` в `.env`
   - Убедитесь в правах доступа к репозиториям
   - Проверьте логи: `docker compose --profile polling logs github-polling`

3. **RAG не индексирует файлы**
   - Проверьте права на запись в `/app/data/index`
   - Убедитесь в корректности ChromaDB

4. **Docker сеть недоступна**
   - Убедитесь, что сеть `homelab` создана
   - Запустите сначала: `./scripts/20_deploy_core.sh`

5. **База данных не подключается**
   - Проверьте статус контейнера `agent-db`
   - Проверьте переменную `AGENT_DB_PASSWORD`

### Логи и диагностика

```bash
# Проверка статуса всех сервисов
docker compose ps

# Проверка сети homelab
docker network inspect homelab

# Тест подключения к агенту
curl -f http://your_local_ip:8000/api/health

# Проверка переменных окружения
docker compose exec agent env | grep -E "(GIGACHAT|TAVILY|GITHUB)"

# Вход в контейнер агента
docker compose exec agent bash

# Вход в базу данных
docker compose exec agent-db psql -U agent -d homelab_agent
```

## 📈 Развитие

### Планируемые улучшения

- [ ] Интеграция с Prometheus для метрик
- [ ] Поддержка других LLM провайдеров
- [ ] Расширенная аналитика кода
- [ ] Автоматическое исправление проблем
- [ ] Интеграция с CI/CD системами
- [ ] Мониторинг производительности контейнеров

### Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🤝 Поддержка

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Wiki**: GitHub Wiki

---

**Homelab Agent** - ваш интеллектуальный помощник для домашнего сервера в Docker! 🐳🚀
