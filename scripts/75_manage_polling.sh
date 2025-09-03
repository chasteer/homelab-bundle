#!/usr/bin/env bash
set -euo pipefail

# Скрипт для управления GitHub Polling Service

show_help() {
    cat << 'EOF'
🔧 Управление GitHub Polling Service

Использование: $0 [команда]

Команды:
  start     - Запустить сервис
  stop      - Остановить сервис
  restart   - Перезапустить сервис
  status    - Показать статус
  logs      - Показать логи
  config    - Открыть конфигурацию для редактирования
  add-repo  - Добавить репозиторий для мониторинга
  remove-repo - Удалить репозиторий из мониторинга
  list      - Показать список мониторимых репозиториев
  help      - Показать эту справку

Примеры:
  $0 start
  $0 add-repo microsoft/vscode main
  $0 status
  $0 logs
EOF
}

check_service_exists() {
    if ! systemctl list-unit-files | grep -q "github-polling.service"; then
        echo "❌ GitHub Polling Service не установлен"
        echo "Запустите сначала: scripts/70_setup_github_polling.sh"
        exit 1
    fi
}

start_service() {
    echo "🚀 Запуск GitHub Polling Service..."
    systemctl start github-polling.service
    systemctl status github-polling.service --no-pager -l
}

stop_service() {
    echo "🛑 Остановка GitHub Polling Service..."
    systemctl stop github-polling.service
    echo "✅ Сервис остановлен"
}

restart_service() {
    echo "🔄 Перезапуск GitHub Polling Service..."
    systemctl restart github-polling.service
    systemctl status github-polling.service --no-pager -l
}

show_status() {
    echo "📊 Статус GitHub Polling Service:"
    echo "=================================="
    systemctl status github-polling.service --no-pager -l
    
    echo ""
    echo "📋 Конфигурация:"
    if [ -f "/etc/homelab/github/polling.conf" ]; then
        echo "✅ Конфигурационный файл найден"
        echo "📁 Путь: /etc/homelab/github/polling.conf"
    else
        echo "❌ Конфигурационный файл не найден"
    fi
    
    echo ""
    echo "📊 Последние проверки:"
    if [ -f "/var/lib/homelab/github_last_check.json" ]; then
        echo "✅ Файл состояния найден"
        echo "📁 Путь: /var/lib/homelab/github_last_check.json"
    else
        echo "❌ Файл состояния не найден"
    fi
}

show_logs() {
    echo "📋 Логи GitHub Polling Service:"
    echo "================================"
    journalctl -u github-polling.service -f --no-pager -l
}

edit_config() {
    if [ -z "${EDITOR:-}" ]; then
        if command -v nano >/dev/null 2>&1; then
            EDITOR=nano
        elif command -v vim >/dev/null 2>&1; then
            EDITOR=vim
        elif command -v vi >/dev/null 2>&1; then
            EDITOR=vi
        else
            echo "❌ Не найден редактор. Установите EDITOR или nano/vim/vi"
            exit 1
        fi
    fi
    
    echo "📝 Открытие конфигурации в $EDITOR..."
    $EDITOR /etc/homelab/github/polling.conf
    
    echo "✅ Конфигурация отредактирована"
    echo "🔄 Перезапустите сервис для применения изменений: $0 restart"
}

add_repository() {
    if [ $# -lt 2 ]; then
        echo "❌ Недостаточно параметров"
        echo "Использование: $0 add-repo owner/repo branch [webhook_url] [secret]"
        echo "Пример: $0 add-repo microsoft/vscode main https://your-domain.com/webhook/github your_secret"
        exit 1
    fi
    
    owner_repo="$1"
    branch="$2"
    webhook_url="${3:-https://localhost:8000/webhook/github}"
    secret="${4:-}"
    
    # Проверяем формат owner/repo
    if [[ ! "$owner_repo" =~ ^[^/]+/[^/]+$ ]]; then
        echo "❌ Неверный формат owner/repo. Используйте: owner/repo"
        exit 1
    fi
    
    # Формируем строку конфигурации
    config_line="$owner_repo:$branch:$webhook_url"
    if [ -n "$secret" ]; then
        config_line="$config_line:$secret"
    fi
    
    # Добавляем в конфигурацию
    echo "" >> /etc/homelab/github/polling.conf
    echo "# Добавлено через скрипт управления" >> /etc/homelab/github/polling.conf
    echo "$config_line" >> /etc/homelab/github/polling.conf
    
    echo "✅ Репозиторий $owner_repo добавлен для мониторинга"
    echo "📝 Конфигурация обновлена"
    echo "🔄 Перезапустите сервис для применения изменений: $0 restart"
}

remove_repository() {
    if [ $# -lt 1 ]; then
        echo "❌ Не указан репозиторий для удаления"
        echo "Использование: $0 remove-repo owner/repo"
        echo "Пример: $0 remove-repo microsoft/vscode"
        exit 1
    fi
    
    owner_repo="$1"
    
    # Создаем временный файл
    temp_file=$(mktemp)
    
    # Копируем все строки кроме указанного репозитория
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^$owner_repo: ]]; then
            echo "$line" >> "$temp_file"
        fi
    done < /etc/homelab/github/polling.conf
    
    # Заменяем оригинальный файл
    mv "$temp_file" /etc/homelab/github/polling.conf
    
    echo "✅ Репозиторий $owner_repo удален из мониторинга"
    echo "🔄 Перезапустите сервис для применения изменений: $0 restart"
}

list_repositories() {
    echo "📋 Мониторимые репозитории:"
    echo "============================="
    
    if [ ! -f "/etc/homelab/github/polling.conf" ]; then
        echo "❌ Конфигурационный файл не найден"
        exit 1
    fi
    
    count=0
    while IFS= read -r line; do
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ "$line" =~ ^[^#] && "$line" =~ : ]]; then
            count=$((count + 1))
            parts=(${line//:/ })
            owner_repo="${parts[0]}"
            branch="${parts[1]}"
            webhook="${parts[2]}"
            secret="${parts[3]:-не задан}"
            
            echo "$count. $owner_repo (ветка: $branch)"
            echo "   Webhook: $webhook"
            echo "   Секрет: $secret"
            echo ""
        fi
    done < /etc/homelab/github/polling.conf
    
    if [ $count -eq 0 ]; then
        echo "ℹ️  Нет настроенных репозиториев"
        echo "Добавьте репозиторий: $0 add-repo owner/repo branch"
    fi
}

# Основная логика
case "${1:-help}" in
    start)
        check_service_exists
        start_service
        ;;
    stop)
        check_service_exists
        stop_service
        ;;
    restart)
        check_service_exists
        restart_service
        ;;
    status)
        check_service_exists
        show_status
        ;;
    logs)
        check_service_exists
        show_logs
        ;;
    config)
        check_service_exists
        edit_config
        ;;
    add-repo)
        check_service_exists
        shift
        add_repository "$@"
        ;;
    remove-repo)
        check_service_exists
        shift
        remove_repository "$@"
        ;;
    list)
        check_service_exists
        list_repositories
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
