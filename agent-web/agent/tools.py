"""
Пользовательские инструменты для Homelab Agent
Включает: Tavily поиск, Wikipedia, системную информацию, Docker compose анализ, GitHub
"""

import os
import re
import yaml
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

import requests
import json
import re
import ast
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

# Инициализация Tavily поиска
tavily_search = TavilySearchResults(max_results=5)

@tool
def analyze_code_quality(code: str, language: str = "python") -> str:
    """Анализ качества кода на предмет критических ошибок, стиля и наименований.
    
    Args:
        code: Исходный код для анализа
        language: Язык программирования (python, javascript, etc.)
    """
    issues = []
    
    try:
        if language.lower() == "python":
            # Анализ Python кода
            issues.extend(_analyze_python_code(code))
        else:
            # Базовый анализ для других языков
            issues.extend(_analyze_generic_code(code))
            
        if not issues:
            return "✅ Код не содержит критических проблем"
        
        result = "🔍 **Найденные проблемы:**\n\n"
        for i, issue in enumerate(issues, 1):
            result += f"{i}. **{issue['type']}** (строка {issue.get('line', '?')}): {issue['message']}\n"
            if issue.get('suggestion'):
                result += f"   💡 **Рекомендация**: {issue['suggestion']}\n"
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Ошибка при анализе кода: {str(e)}"


def _analyze_python_code(code: str) -> List[Dict[str, Any]]:
    """Анализ Python кода на предмет проблем"""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Проверка на необработанные исключения
        if re.search(r'except\s*:', line):
            issues.append({
                'type': 'Критическая ошибка',
                'line': i,
                'message': 'Необработанное исключение - используйте конкретный тип исключения',
                'suggestion': 'Замените на except SpecificException: или except Exception as e:'
            })
        
        # Проверка на bare except
        if re.search(r'except\s*$', line):
            issues.append({
                'type': 'Критическая ошибка',
                'line': i,
                'message': 'Bare except - перехватывает все исключения включая KeyboardInterrupt',
                'suggestion': 'Используйте except Exception: или конкретный тип исключения'
            })
        
        # Проверка на print в коде (не в отладочных блоках)
        if re.search(r'print\s*\(', line) and not re.search(r'#\s*debug|#\s*DEBUG', line):
            issues.append({
                'type': 'Стиль кода',
                'line': i,
                'message': 'Использование print() в коде',
                'suggestion': 'Используйте logging вместо print()'
            })
        
        # Проверка на длинные строки
        if len(line) > 120:
            issues.append({
                'type': 'Стиль кода',
                'line': i,
                'message': f'Строка слишком длинная ({len(line)} символов)',
                'suggestion': 'Разбейте на несколько строк или используйте более короткие имена'
            })
        
        # Проверка на несоответствие PEP 8 в именах переменных
        if re.search(r'[A-Z][a-z]*[A-Z]', line) and not re.search(r'class\s+[A-Z]|def\s+[A-Z]', line):
            camel_case_vars = re.findall(r'\b[a-z]+[A-Z][a-zA-Z]*\b', line)
            for var in camel_case_vars:
                issues.append({
                    'type': 'Стиль кода',
                    'line': i,
                    'message': f'Переменная "{var}" использует camelCase',
                    'suggestion': 'Используйте snake_case: ' + re.sub(r'([a-z])([A-Z])', r'\1_\2', var).lower()
                })
        
        # Проверка на магические числа
        if re.search(r'\b\d{3,}\b', line) and not re.search(r'#\s*port|#\s*timeout|#\s*version', line):
            issues.append({
                'type': 'Стиль кода',
                'line': i,
                'message': 'Магическое число в коде',
                'suggestion': 'Вынесите в константу с описательным именем'
            })
    
    # Проверка синтаксиса
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append({
            'type': 'Критическая ошибка',
            'line': e.lineno,
            'message': f'Синтаксическая ошибка: {e.msg}',
            'suggestion': 'Исправьте синтаксическую ошибку'
        })
    
    return issues


def _analyze_generic_code(code: str) -> List[Dict[str, Any]]:
    """Базовый анализ для других языков программирования"""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        
        # Проверка на длинные строки
        if len(line) > 120:
            issues.append({
                'type': 'Стиль кода',
                'line': i,
                'message': f'Строка слишком длинная ({len(line)} символов)',
                'suggestion': 'Разбейте на несколько строк'
            })
        
        # Проверка на TODO/FIXME без описания
        if re.search(r'(TODO|FIXME|HACK):\s*$', line, re.IGNORECASE):
            issues.append({
                'type': 'Стиль кода',
                'line': i,
                'message': 'TODO/FIXME без описания',
                'suggestion': 'Добавьте описание того, что нужно сделать'
            })
    
    return issues


@tool
def get_system_info() -> str:
    """Получить информацию о системе: имя пользователя, операционная система, текущая директория."""
    try:
        info = []
        
        # Имя пользователя
        username = os.getenv("USER", "unknown")
        info.append(f"👤 **Пользователь**: {username}")
        
        # Операционная система
        import platform
        system = platform.system()
        version = platform.version()
        machine = platform.machine()
        info.append(f"💻 **ОС**: {system} {version} ({machine})")
        
        # Текущая директория
        current_dir = Path.cwd()
        info.append(f"📂 **Текущая директория**: {current_dir}")
        
        # Время
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info.append(f"⏰ **Текущее время**: {current_time}")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"Ошибка при получении системной информации: {str(e)}"


@tool
def docker_compose_lint(yaml_text: str) -> Dict[str, Any]:
    """Анализ Docker Compose файла на предмет ошибок и рекомендаций.
    
    Args:
        yaml_text: Содержимое docker-compose.yml файла
    """
    issues = []
    warnings = []
    
    try:
        data = yaml.safe_load(yaml_text) or {}
    except Exception as e:
        return {"ok": False, "error": f"YAML parse error: {e}"}
    
    if "services" not in data:
        issues.append("Нет ключа 'services' в compose.")
    else:
        for name, svc in (data.get("services") or {}).items():
            svc = svc or {}
            
            # Проверяем restart policy
            if "restart" not in svc:
                warnings.append(f"{name}: рекомендуется 'restart: unless-stopped'")
            
            # Проверяем healthcheck
            if "healthcheck" not in svc:
                warnings.append(f"{name}: добавь healthcheck")
            
            # Проверяем volumes
            if "volumes" not in svc:
                warnings.append(f"{name}: укажи volumes для конфигов/данных")
            
            # Проверяем порты
            for p in svc.get("ports", []) or []:
                if ":" not in str(p):
                    warnings.append(f"{name}: порт '{p}' лучше 'HOST:CONTAINER'")
    
    return {"ok": True, "issues": issues, "warnings": warnings}


@tool
def port_conflict_scan(yaml_texts: List[str]) -> Dict[str, Any]:
    """Сканирование конфликтов портов в Docker Compose файлах.
    
    Args:
        yaml_texts: Список содержимого docker-compose файлов
    """
    conflicts = []
    seen = {}
    
    for i, y in enumerate(yaml_texts):
        try:
            data = yaml.safe_load(y) or {}
        except Exception as e:
            conflicts.append(f"Файл {i}: ошибка парсинга: {e}")
            continue
        
        for name, svc in (data.get("services") or {}).items():
            for p in (svc.get("ports") or []):
                ps = str(p).split(":")
                host = ps[-2] if len(ps) == 3 else ps[0]
                host = host.strip()
                
                if not host or host == "None":
                    continue
                
                if host in seen:
                    conflicts.append(f"Порт {host} уже занят сервисом {seen[host]} (конфликт с {name})")
                else:
                    seen[host] = name
    
    return {"conflicts": conflicts}


@tool
def ufw_rule_advisor(services: Dict[str, int], lan_cidr: str = "192.168.0.0/16") -> List[str]:
    """Генерация правил UFW для сервисов homelab.
    
    Args:
        services: Словарь сервисов и их портов
        lan_cidr: CIDR локальной сети
    """
    return [f"sudo ufw allow from {lan_cidr} to any port {port} proto tcp  # {name}" 
            for name, port in services.items()]


@tool
def github_comment_pr(owner: str, repo: str, pr_number: int, comment: str) -> str:
    """Добавить комментарий к pull request в GitHub.
    
    Args:
        owner: Владелец репозитория
        repo: Название репозитория
        pr_number: Номер pull request
        comment: Текст комментария
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "❌ Не задан GITHUB_TOKEN в переменных окружения"
        
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {"body": comment}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            return f"✅ Комментарий добавлен к PR #{pr_number} в {owner}/{repo}"
        else:
            return f"❌ Ошибка добавления комментария: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Ошибка при добавлении комментария: {str(e)}"


@tool
def github_get_pr_files(owner: str, repo: str, pr_number: int) -> str:
    """Получить список измененных файлов в pull request.
    
    Args:
        owner: Владелец репозитория
        repo: Название репозитория
        pr_number: Номер pull request
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "❌ Не задан GITHUB_TOKEN в переменных окружения"
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            files = response.json()
            
            result = f"📁 **Измененные файлы в PR #{pr_number}:**\n\n"
            
            for file in files:
                filename = file.get('filename', 'Unknown')
                status = file.get('status', 'Unknown')
                additions = file.get('additions', 0)
                deletions = file.get('deletions', 0)
                
                result += f"📄 **{filename}**\n"
                result += f"   📊 Статус: {status}\n"
                result += f"   ➕ Добавлено: {additions} строк\n"
                result += f"   ➖ Удалено: {deletions} строк\n\n"
            
            return result
        else:
            return f"❌ Ошибка получения файлов: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Ошибка при получении файлов PR: {str(e)}"


@tool
def github_get_file_content(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """Получить содержимое файла из GitHub репозитория.
    
    Args:
        owner: Владелец репозитория
        repo: Название репозитория
        path: Путь к файлу
        ref: Ветка или коммит (по умолчанию main)
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "❌ Не задан GITHUB_TOKEN в переменных окружения"
        
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        params = {"ref": ref}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            file_data = response.json()
            
            if file_data.get('type') == 'file':
                import base64
                content = base64.b64decode(file_data['content']).decode('utf-8')
                
                # Ограничиваем размер для анализа
                if len(content) > 10000:
                    content = content[:10000] + "\n... (файл обрезан, слишком большой)"
                
                return f"📄 **Содержимое файла {path}:**\n\n```\n{content}\n```"
            else:
                return f"❌ {path} не является файлом"
        else:
            return f"❌ Ошибка получения файла: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Ошибка при получении файла: {str(e)}"


@tool
def github_search(action: str, query: str, owner: str = "", repo: str = "") -> str:
    """Поиск и получение информации из GitHub: репозитории, пользователи, код.
    
    Args:
        action: Действие (search_repos, search_users, get_repo_info, search_code)
        query: Поисковый запрос
        owner: Владелец репозитория (для get_repo_info)
        repo: Название репозитория (для get_repo_info)
    """
    try:
        base_url = "https://api.github.com"
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Добавляем токен если есть
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        if action == "search_repos":
            url = f"{base_url}/search/repositories"
            params = {"q": query, "sort": "stars", "order": "desc", "per_page": 5}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                repos = data.get("items", [])
                
                result = f"🔍 **Найдено репозиториев**: {data.get('total_count', 0)}\n\n"
                
                for repo_item in repos[:5]:
                    result += f"📦 **{repo_item['full_name']}**\n"
                    result += f"   ⭐ {repo_item['stargazers_count']} звезд\n"
                    result += f"   📝 {repo_item['description'] or 'Нет описания'}\n"
                    result += f"   🔗 {repo_item['html_url']}\n\n"
                
                return result
            else:
                return f"❌ Ошибка поиска репозиториев: {response.status_code}"
        
        elif action == "search_users":
            url = f"{base_url}/search/users"
            params = {"q": query, "sort": "followers", "order": "desc", "per_page": 5}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("items", [])
                
                result = f"🔍 **Найдено пользователей**: {data.get('total_count', 0)}\n\n"
                
                for user in users[:5]:
                    result += f"👤 **{user['login']}**\n"
                    result += f"   🔗 {user['html_url']}\n"
                    result += f"   📊 Score: {user['score']}\n\n"
                
                return result
            else:
                return f"❌ Ошибка поиска пользователей: {response.status_code}"
        
        elif action == "get_repo_info":
            if not owner or not repo:
                return "❌ Для получения информации о репозитории нужны параметры owner и repo"
            
            url = f"{base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                result = f"📦 **{repo_data['full_name']}**\n\n"
                result += f"📝 **Описание**: {repo_data['description'] or 'Нет описания'}\n"
                result += f"⭐ **Звезды**: {repo_data['stargazers_count']}\n"
                result += f"🍴 **Форки**: {repo_data['forks_count']}\n"
                result += f"👁️ **Наблюдающие**: {repo_data['watchers_count']}\n"
                result += f"📊 **Размер**: {repo_data['size']} KB\n"
                result += f"💬 **Язык**: {repo_data['language'] or 'Не указан'}\n"
                result += f"🔗 **URL**: {repo_data['html_url']}\n"
                result += f"📅 **Создан**: {repo_data['created_at'][:10]}\n"
                result += f"🔄 **Обновлен**: {repo_data['updated_at'][:10]}\n"
                
                return result
            else:
                return f"❌ Репозиторий {owner}/{repo} не найден"
        
        elif action == "search_code":
            url = f"{base_url}/search/code"
            params = {"q": query, "sort": "indexed", "order": "desc", "per_page": 5}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                code_results = data.get("items", [])
                
                result = f"🔍 **Найдено файлов с кодом**: {data.get('total_count', 0)}\n\n"
                
                for item in code_results[:5]:
                    result += f"📄 **{item['name']}**\n"
                    result += f"   📦 {item['repository']['full_name']}\n"
                    result += f"   🔗 {item['html_url']}\n\n"
                
                return result
            else:
                return f"❌ Ошибка поиска кода: {response.status_code}"
        
        else:
            return "❌ Неизвестное действие. Доступные: search_repos, search_users, get_repo_info, search_code"
            
    except Exception as e:
        return f"❌ Ошибка при работе с GitHub API: {str(e)}"


@tool
def monitor_homelab_services() -> str:
    """Мониторинг состояния сервисов homelab: проверка портов, статуса контейнеров, логов."""
    try:
        import subprocess
        import json
        
        result = []
        result.append("🔍 **Мониторинг сервисов Homelab**\n")
        
        # Проверяем статус Docker контейнеров
        try:
            docker_ps = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
                capture_output=True, text=True, timeout=10
            )
            
            if docker_ps.returncode == 0:
                result.append("🐳 **Docker контейнеры:**")
                lines = docker_ps.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                for line in lines:
                    if line.strip():
                        result.append(f"   {line}")
            else:
                result.append("❌ Ошибка получения статуса Docker")
                
        except Exception as e:
            result.append(f"❌ Ошибка Docker: {str(e)}")
        
        # Проверяем основные порты homelab сервисов
        ports_to_check = {
            "torrserver": 8090,
            "immich-server": 2283,
            "vaultwarden": 8081,
            "uptime-kuma": 3001,
            "jellyfin": 8096,
            "homelab-agent": 8000
        }
        
        result.append("\n🌐 **Проверка портов:**")
        for service, port in ports_to_check.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result_socket = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result_socket == 0:
                    result.append(f"   ✅ {service}:{port} - доступен")
                else:
                    result.append(f"   ❌ {service}:{port} - недоступен")
            except Exception as e:
                result.append(f"   ❓ {service}:{port} - ошибка проверки: {str(e)}")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Ошибка при мониторинге сервисов: {str(e)}"


@tool
def get_weather_info(city: str) -> str:
    """Получить актуальную информацию о погоде в указанном городе.
    
    Args:
        city: Название города (например: Москва, Санкт-Петербург, London)
    """
    try:
        # Используем Tavily для поиска актуальной информации о погоде
        query = f"погода {city} сегодня актуальная температура осадки"
        result = tavily_search.invoke(query)
        
        if result and "❌" not in result:
            return f"🌤️ **Погода в {city}:**\n\n{result}"
        else:
            # Если поиск не дал результатов, используем прямой поиск
            fallback_query = f"weather {city} current temperature conditions"
            fallback_result = tavily_search.invoke(fallback_query)
            return f"🌤️ **Погода в {city}:**\n\n{fallback_result}"
            
    except Exception as e:
        return f"❌ Ошибка получения информации о погоде: {str(e)}"


# Список всех инструментов для удобства импорта
ALL_CUSTOM_TOOLS = [
    analyze_code_quality,
    get_system_info,
    docker_compose_lint,
    port_conflict_scan,
    ufw_rule_advisor,
    github_comment_pr,
    github_get_pr_files,
    github_get_file_content,
    github_search,
    tavily_search,
    get_weather_info,
    monitor_homelab_services
]
