import os
import json
from typing import Dict, List, Any, Optional
from langchain.tools import tool
from .uptime_kuma_api import get_uptime_kuma_api, test_uptime_kuma_connection

@tool
def get_uptime_kuma_monitors() -> str:
    """
    Получает список всех мониторов из Uptime Kuma через API.
    
    Returns:
        str: JSON строка с информацией о мониторах
    """
    try:
        api = get_uptime_kuma_api()
        monitors = api.get_monitors()
        
        if monitors is None:
            return "❌ Не удалось получить данные мониторов из Uptime Kuma API"
        
        # Форматируем результат для лучшей читаемости
        if isinstance(monitors, dict):
            formatted_monitors = []
            for monitor_name, monitor_data in monitors.items():
                formatted_monitors.append({
                    "name": monitor_data.get("name", "Unknown"),
                    "type": monitor_data.get("type", "Unknown"),
                    "url": monitor_data.get("url", "N/A"),
                    "status": monitor_data.get("status", "Unknown"),
                    "status_text": monitor_data.get("status_text", "Unknown")
                })
            return json.dumps(formatted_monitors, indent=2, ensure_ascii=False)
        else:
            return json.dumps(monitors, indent=2, ensure_ascii=False)
            
    except Exception as e:
        return f"❌ Ошибка при получении мониторов: {str(e)}"

@tool
def get_uptime_kuma_metrics() -> str:
    """
    Получает метрики Uptime Kuma в формате Prometheus.
    
    Returns:
        str: Метрики в формате Prometheus
    """
    try:
        api = get_uptime_kuma_api()
        metrics = api.get_metrics()
        
        if metrics is None:
            return "❌ Не удалось получить метрики из Uptime Kuma API"
        
        if isinstance(metrics, dict) and "content" in metrics:
            return metrics["content"]
        else:
            return str(metrics)
            
    except Exception as e:
        return f"❌ Ошибка при получении метрик: {str(e)}"

@tool
def test_uptime_kuma_api() -> str:
    """
    Тестирует подключение к Uptime Kuma API и возвращает статус.
    
    Returns:
        str: Результат тестирования API
    """
    try:
        result = test_uptime_kuma_connection()
        
        status = "✅ API доступен" if result["connected"] else "❌ API недоступен"
        monitors_info = f"Мониторов: {result['monitors_count']}" if result["monitors_count"] > 0 else "Мониторы не найдены"
        
        response = f"""
🔍 **Тест подключения к Uptime Kuma API**

📊 **Статус**: {status}
📈 **Мониторы**: {monitors_info}
🔑 **API ключ**: {'Настроен' if os.getenv('UPTIME_KUMA_API') else 'Не настроен'}
🌐 **URL**: {os.getenv('UPTIME_KUMA_URL', 'Не настроен')}
"""
        
        if result["error"]:
            response += f"\n❌ **Ошибка**: {result['error']}"
        
        return response
        
    except Exception as e:
        return f"❌ Ошибка при тестировании API: {str(e)}"

@tool
def get_monitor_badge(monitor_id: int, badge_type: str = "uptime") -> str:
    """
    Получает бейдж для конкретного монитора.
    
    Args:
        monitor_id (int): ID монитора
        badge_type (str): Тип бейджа (uptime, response, status)
    
    Returns:
        str: URL бейджа или сообщение об ошибке
    """
    try:
        api = get_uptime_kuma_api()
        badge = api.get_badge(monitor_id, badge_type)
        
        if badge is None:
            return f"❌ Не удалось получить бейдж для монитора {monitor_id}"
        
        if isinstance(badge, dict) and "content" in badge:
            return badge["content"]
        else:
            return str(badge)
            
    except Exception as e:
        return f"❌ Ошибка при получении бейджа: {str(e)}"

@tool
def get_monitor_heartbeat(monitor_id: int, limit: int = 10) -> str:
    """
    Получает последние heartbeat данные для монитора.
    
    Args:
        monitor_id (int): ID монитора
        limit (int): Количество записей (по умолчанию 10)
    
    Returns:
        str: JSON строка с данными heartbeat
    """
    try:
        api = get_uptime_kuma_api()
        heartbeats = api.get_heartbeat_data(monitor_id, limit)
        
        if heartbeats is None:
            return f"❌ Не удалось получить heartbeat данные для монитора {monitor_id}"
        
        return json.dumps(heartbeats, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении heartbeat данных: {str(e)}"

# Список всех инструментов для экспорта
UPTIME_KUMA_TOOLS = [
    get_uptime_kuma_monitors,
    get_uptime_kuma_metrics,
    test_uptime_kuma_api,
    get_monitor_badge,
    get_monitor_heartbeat
]
