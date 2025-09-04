#!/usr/bin/env bash
set -euo pipefail

# Скрипт управления Homelab Agent

cd "$(dirname "$0")/../agent-web"

show_help() {
    cat << 'EOF'
🔧 Управление Homelab Agent

Использование: $0 [команда]

Команды:
  start     - Запустить агента
  stop      - Остановить агента
  restart   - Перезапустить агента
  status    - Показать статус
  logs      - Показать логи
  build     - Пересобрать образ
  update    - Обновить код и пересобрать
  shell     - Войти в контейнер агента
  db-shell  - Войти в контейнер базы данных
  backup    - Создать резервную копию данных
  restore   - Восстановить данные из резервной копии
  health    - Проверить здоровье сервиса
  services  - Показать статус всех сервисов homelab
  help      - Показать эту справку

Примеры:
  $0 start
  $0 logs
  $0 health
  $0 services
EOF
}

check_env() {
    if [ ! -f ".env" ]; then
        echo "❌ Файл .env не найден"
        echo "Создайте его на основе .env.example и заполните переменные"
        exit 1
    fi
}

start_agent() {
    echo "🚀 Запуск Homelab Agent..."
    sudo docker compose up -d
    echo "✅ Агент запущен"
    show_status
}

stop_agent() {
    echo "🛑 Остановка Homelab Agent..."
    sudo docker compose down
    echo "✅ Агент остановлен"
}

restart_agent() {
    echo "🔄 Перезапуск Homelab Agent..."
    sudo docker compose restart
    echo "✅ Агент перезапущен"
    show_status
}

show_status() {
    echo "📊 Статус Homelab Agent:"
    echo "=========================="
    sudo docker compose ps
    
    echo ""
    echo "🌐 Веб-интерфейс: http://${HOMELAB_HOST:-your_local_ip}:8000"
    echo "🔍 Health check: http://${HOMELAB_HOST:-your_local_ip}:8000/api/health"
}

show_logs() {
    echo "📋 Логи Homelab Agent:"
    echo "======================="
    sudo docker compose logs -f
}

build_agent() {
    echo "🔨 Пересборка образа агента..."
    sudo docker compose build --no-cache
    echo "✅ Образ пересобран"
}

update_agent() {
    echo "📥 Обновление кода агента..."
    git pull origin main || echo "⚠️  Не удалось обновить код из git"
    
    echo "🔨 Пересборка образа..."
    sudo docker compose build --no-cache
    
    echo "🔄 Перезапуск с новым образом..."
    sudo docker compose up -d
    
    echo "✅ Агент обновлен и перезапущен"
}

shell_agent() {
    echo "🐚 Вход в контейнер агента..."
    sudo docker compose exec agent bash
}

shell_db() {
    echo "🐚 Вход в контейнер базы данных..."
    sudo docker compose exec agent-db psql -U agent -d homelab_agent
}

backup_data() {
    echo "💾 Создание резервной копии данных..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="backups/agent_${timestamp}"
    
    mkdir -p "$backup_dir"
    
    # Резервная копия базы данных
    sudo docker compose exec -T agent-db pg_dump -U agent homelab_agent > "$backup_dir/database.sql"
    
    # Резервная копия файлов
    tar -czf "$backup_dir/data.tar.gz" data/ logs/ github-config/
    
    echo "✅ Резервная копия создана: $backup_dir"
}

restore_data() {
    if [ $# -eq 0 ]; then
        echo "❌ Укажите путь к резервной копии"
        echo "Использование: $0 restore /path/to/backup"
        exit 1
    fi
    
    backup_path="$1"
    if [ ! -d "$backup_path" ]; then
        echo "❌ Директория резервной копии не найдена: $backup_path"
        exit 1
    fi
    
    echo "🔄 Восстановление данных из: $backup_path"
    
    # Восстанавливаем базу данных
    if [ -f "$backup_path/database.sql" ]; then
        echo "📊 Восстановление базы данных..."
        sudo docker compose exec -T agent-db psql -U agent -d homelab_agent < "$backup_path/database.sql"
    fi
    
    # Восстанавливаем файлы
    if [ -f "$backup_path/data.tar.gz" ]; then
        echo "📁 Восстановление файлов..."
        tar -xzf "$backup_path/data.tar.gz"
    fi
    
    echo "✅ Данные восстановлены"
}

check_health() {
    echo "🔍 Проверка здоровья Homelab Agent..."
    
    if ! curl -f http://${HOMELAB_HOST:-your_local_ip}:8000/api/health >/dev/null 2>&1; then
        echo "❌ Сервис не отвечает"
        return 1
    fi
    
            response=$(curl -s http://${HOMELAB_HOST:-your_local_ip}:8000/api/health)
    echo "✅ Сервис отвечает"
    echo "📊 Статус: $response"
}

show_services() {
    echo "🔍 Получение статуса всех сервисов homelab..."
    
    if ! curl -f http://${HOMELAB_HOST:-your_local_ip}:8000/api/services >/dev/null 2>&1; then
        echo "❌ Не удалось получить статус сервисов"
        return 1
    fi
    
            response=$(curl -s http://${HOMELAB_HOST:-your_local_ip}:8000/api/services)
    echo "📊 Статус сервисов:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
}

# Основная логика
case "${1:-help}" in
    start)
        check_env
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    restart)
        check_env
        restart_agent
        ;;
    status)
        check_env
        show_status
        ;;
    logs)
        check_env
        show_logs
        ;;
    build)
        check_env
        build_agent
        ;;
    update)
        check_env
        update_agent
        ;;
    shell)
        check_env
        shell_agent
        ;;
    db-shell)
        check_env
        shell_db
        ;;
    backup)
        check_env
        backup_data
        ;;
    restore)
        check_env
        shift
        restore_data "$@"
        ;;
    health)
        check_env
        check_health
        ;;
    services)
        check_env
        show_services
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

