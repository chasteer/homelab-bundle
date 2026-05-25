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




@tool
def send_uptime_alert(service_name: str, status: str, details: str) -> str:
    """Отправить уведомление о проблеме в Uptime Kuma на VPS для дальнейшей обработки.
    
    Args:
        service_name: Название сервиса с проблемой
        status: Статус (down, error, warning)
        details: Детали проблемы
    """
    try:
        import requests
        
        # Данные для отправки
        alert_data = {
            "source": "homelab_agent",
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "status": status,
            "details": details,
            "host": os.environ.get("HOMELAB_HOST", "localhost")
        }
        
        # Отправляем на VPS
        vps_url = os.environ.get("VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts")
        
        response = requests.post(
            vps_url,
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return f"✅ Уведомление отправлено на VPS для сервиса {service_name}"
        else:
            return f"❌ Ошибка отправки на VPS: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Ошибка отправки уведомления: {str(e)}"


@tool
def generate_uptime_report() -> str:
    """Сгенерировать полный отчет о состоянии системы и предложить действия по устранению проблем."""
    try:
        # Получаем данные мониторинга из Uptime Kuma
        from .uptime_kuma_tools import get_uptime_kuma_monitors
        monitoring_data = get_uptime_kuma_monitors.invoke({})
        
        # Анализируем и генерируем рекомендации
        report = []
        report.append("📋 **ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ**\n")
        report.append("📊 **Данные из Uptime Kuma:**")
        report.append(str(monitoring_data))
        
        # Анализируем проблемы и предлагаем решения
        if "❌" in monitoring_data:
            report.append("\n🔧 **РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ:**")
            
            if "uptime-kuma" in monitoring_data.lower():
                report.append("   • Проверить логи Uptime Kuma: `docker logs uptime-kuma`")
                report.append("   • Перезапустить контейнер: `docker restart uptime-kuma`")
            
            if "jellyfin" in monitoring_data.lower():
                report.append("   • Проверить доступность медиа-файлов")
                report.append("   • Проверить права доступа к папкам")
            
            if "immich" in monitoring_data.lower():
                report.append("   • Проверить состояние базы данных PostgreSQL")
                report.append("   • Проверить доступность Redis")
            
            if "vaultwarden" in monitoring_data.lower():
                report.append("   • Проверить права доступа к папке данных")
                report.append("   • Проверить конфигурацию")
            
            report.append("\n📞 **УВЕДОМЛЕНИЯ:**")
            report.append("   • Отправлено на VPS для обработки")
            report.append("   • Будет переслано в Telegram")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"❌ Ошибка генерации отчета: {str(e)}"


@tool
def analyze_incident_with_llm(incident_data: str) -> str:
    """Анализ инцидента Uptime Kuma с использованием LLM и RAG.
    
    Args:
        incident_data: JSON строка с данными об инциденте (монитор, статус, тип, URL, сообщение)
    
    Returns:
        Детальный анализ инцидента с рекомендациями по устранению
    """
    try:
        import json
        from datetime import datetime
        
        # Парсим данные инцидента
        data = json.loads(incident_data)
        monitor_name = data.get('monitor_name', 'Unknown')
        status = data.get('status', 'unknown')
        monitor_type = data.get('monitor_type', 'unknown')
        monitor_url = data.get('monitor_url', 'N/A')
        message = data.get('message', 'No message')
        timestamp = data.get('datetime', datetime.now().isoformat())
        
        # Ищем похожие случаи в RAG
        from .rag import query_logs, add_log_to_rag
        
        # Поиск похожих инцидентов
        similar_incidents = query_logs(f"incident {monitor_name} {status} {monitor_type}", k=3)
        
        # Формируем контекст для LLM
        context = f"""
ИНЦИДЕНТ:
- Монитор: {monitor_name}
- Статус: {status}
- Тип: {monitor_type}
- URL: {monitor_url}
- Сообщение: {message}
- Время: {timestamp}

ПОХОЖИЕ СЛУЧАИ ИЗ ИСТОРИИ:
"""
        
        if similar_incidents and not similar_incidents[0].get('error'):
            for i, incident in enumerate(similar_incidents, 1):
                context += f"\n{i}. {incident['document'][:200]}..."
        else:
            context += "\nПохожих случаев в истории не найдено."
        
        # Добавляем технический контекст
        context += f"""

ТЕХНИЧЕСКИЙ КОНТЕКСТ:
- Тип монитора: {monitor_type}
- Время инцидента: {timestamp}
- Текущий статус: {status}

ПРОСЬБА:
Проведи детальный анализ инцидента и предоставь:
1. Анализ возможных причин
2. Пошаговые рекомендации по устранению
3. Команды для диагностики
4. Профилактические меры
5. Оценку серьезности инцидента

Используй технический опыт и найденную информацию для максимально точного анализа.
"""
        
        # Записываем инцидент в базу данных
        incident_log = f"""
ИНЦИДЕНТ UPTIME KUMA:
Монитор: {monitor_name}
Статус: {status}
Тип: {monitor_type}
URL: {monitor_url}
Сообщение: {message}
Время: {timestamp}
Анализ: Запрос на LLM анализ
"""
        
        log_metadata = {
            "source": "uptime_kuma_webhook",
            "kind": "incident_analysis",
            "monitor_name": monitor_name,
            "status": status,
            "monitor_type": monitor_type,
            "timestamp": timestamp
        }
        
        add_log_to_rag(incident_log, log_metadata)
        
        # Возвращаем контекст для LLM анализа
        return f"""
🔍 **ЗАПРОС НА LLM АНАЛИЗ ИНЦИДЕНТА**

📊 **Данные инцидента:**
- Монитор: {monitor_name}
- Статус: {status}
- Тип: {monitor_type}
- URL: {monitor_url}
- Сообщение: {message}
- Время: {timestamp}

📚 **Контекст для анализа:**
{context}

💡 **Следующий шаг:** Используй этот контекст для генерации детального анализа через LLM.
"""
        
    except Exception as e:
        return f"❌ Ошибка анализа инцидента: {str(e)}"

@tool
def search_incident_history(query: str) -> str:
    """Поиск по истории инцидентов в базе данных.
    
    Args:
        query: Поисковый запрос
    
    Returns:
        Результаты поиска по истории инцидентов
    """
    try:
        from .rag import query_logs
        
        # Поиск в логах
        results = query_logs(query, k=5)
        
        if not results or results[0].get('error'):
            return f"🔍 По запросу '{query}' ничего не найдено."
        
        # Формируем результат
        response = f"🔍 **Результаты поиска по запросу: '{query}'**\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('document', '')
            
            response += f"**{i}. {metadata.get('source', 'Unknown')}**\n"
            response += f"Тип: {metadata.get('kind', 'Unknown')}\n"
            if metadata.get('monitor_name'):
                response += f"Монитор: {metadata['monitor_name']}\n"
            if metadata.get('status'):
                response += f"Статус: {metadata['status']}\n"
            response += f"Содержание: {content[:200]}...\n\n"
        
        return response
        
    except Exception as e:
        return f"❌ Ошибка поиска по истории: {str(e)}"

@tool
def get_incident_statistics() -> str:
    """Получение статистики по инцидентам.
    
    Returns:
        Статистика по инцидентам из базы данных
    """
    try:
        from .rag import get_recent_context
        
        # Получаем недавний контекст
        recent_context = get_recent_context(k=20)
        
        if not recent_context or recent_context[0].get('error'):
            return "📊 Статистика недоступна."
        
        # Анализируем контекст
        incident_count = 0
        down_count = 0
        up_count = 0
        monitor_types = {}
        sources = {}
        
        for item in recent_context:
            if item.get('kind') == 'incident_analysis':
                incident_count += 1
                
                # Анализируем содержимое
                content = item.get('content', '')
                if 'Status: down' in content:
                    down_count += 1
                elif 'Status: up' in content:
                    up_count += 1
                
                # Типы мониторов
                if 'docker' in content.lower():
                    monitor_types['docker'] = monitor_types.get('docker', 0) + 1
                elif 'http' in content.lower():
                    monitor_types['http'] = monitor_types.get('http', 0) + 1
                elif 'tcp' in content.lower():
                    monitor_types['tcp'] = monitor_types.get('tcp', 0) + 1
                
                # Источники
                source = item.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
        
        # Формируем статистику
        stats = f"""
📊 **СТАТИСТИКА ПО ИНЦИДЕНТАМ**

🔢 **Общее количество:** {incident_count}
🔴 **Падения (down):** {down_count}
🟢 **Восстановления (up):** {up_count}

🖥️ **Типы мониторов:**
"""
        
        for monitor_type, count in monitor_types.items():
            stats += f"   • {monitor_type}: {count}\n"
        
        stats += f"\n📡 **Источники:**\n"
        
        for source, count in sources.items():
            stats += f"   • {source}: {count}\n"
        
        if incident_count > 0:
            uptime_percentage = (up_count / incident_count) * 100
            stats += f"\n📈 **Процент восстановлений:** {uptime_percentage:.1f}%"
        
        return stats
        
    except Exception as e:
        return f"❌ Ошибка получения статистики: {str(e)}"


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
    send_uptime_alert,
    generate_uptime_report,
    analyze_incident_with_llm,
    search_incident_history,
    get_incident_statistics
]
