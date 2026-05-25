import json
from typing import Dict, List, Any, Optional
from langchain.tools import tool
from .uptime_kuma_socketio import get_uptime_kuma_client, test_uptime_kuma_socketio

@tool
def get_uptime_kuma_monitors_socketio() -> str:
    """
    Получает список всех мониторов из Uptime Kuma через Socket.io API.
    Возвращает детальную информацию о каждом мониторе.
    
    Returns:
        str: JSON строка с информацией о мониторах
    """
    try:
        client = get_uptime_kuma_client()
        monitors = client.get_monitors()
        
        if not monitors:
            return "❌ Не удалось получить данные мониторов из Uptime Kuma через Socket.io"
        
        # Форматируем результат для лучшей читаемости
        formatted_monitors = []
        for monitor_id, monitor_data in monitors.items():
            formatted_monitor = {
                "id": monitor_id,
                "name": monitor_data.get("name", "Unknown"),
                "type": monitor_data.get("type", "Unknown"),
                "url": monitor_data.get("url", "N/A"),
                "hostname": monitor_data.get("hostname", "N/A"),
                "port": monitor_data.get("port", "N/A"),
                "active": monitor_data.get("active", False),
                "interval": monitor_data.get("interval", "N/A"),
                "retryInterval": monitor_data.get("retryInterval", "N/A"),
                "maxretries": monitor_data.get("maxretries", "N/A"),
                "tags": monitor_data.get("tags", []),
                "notificationIDList": monitor_data.get("notificationIDList", {}),
                "accepted_statuscodes": monitor_data.get("accepted_statuscodes_json", "[]"),
                "conditions": monitor_data.get("conditions", "[]")
            }
            formatted_monitors.append(formatted_monitor)
        
        return json.dumps(formatted_monitors, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении мониторов через Socket.io: {str(e)}"

@tool
def get_monitor_details_socketio(monitor_id: int) -> str:
    """
    Получает детальную информацию о конкретном мониторе через Socket.io API.
    
    Args:
        monitor_id (int): ID монитора
    
    Returns:
        str: JSON строка с детальной информацией о мониторе
    """
    try:
        client = get_uptime_kuma_client()
        monitor = client.get_monitor_by_id(monitor_id)
        
        if not monitor:
            return f"❌ Монитор с ID {monitor_id} не найден"
        
        # Получаем дополнительную информацию
        heartbeats = client.get_monitor_heartbeats(monitor_id, 10)
        uptime_stats = client.get_uptime_stats(monitor_id)
        
        result = {
            "monitor": monitor,
            "recent_heartbeats": heartbeats,
            "uptime_stats": uptime_stats
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении деталей монитора {monitor_id}: {str(e)}"

@tool
def get_monitor_heartbeats_socketio(monitor_id: int, limit: int = 20) -> str:
    """
    Получает последние heartbeat данные для монитора через Socket.io API.
    
    Args:
        monitor_id (int): ID монитора
        limit (int): Количество записей (по умолчанию 20)
    
    Returns:
        str: JSON строка с данными heartbeat
    """
    try:
        client = get_uptime_kuma_client()
        heartbeats = client.get_monitor_heartbeats(monitor_id, limit)
        
        if not heartbeats:
            return f"❌ Не удалось получить heartbeat данные для монитора {monitor_id}"
        
        # Форматируем heartbeat данные
        formatted_heartbeats = []
        for hb in heartbeats:
            formatted_hb = {
                "monitorID": hb.get("monitorID"),
                "status": hb.get("status"),  # 0=DOWN, 1=UP, 2=PENDING, 3=MAINTENANCE
                "status_text": {0: "DOWN", 1: "UP", 2: "PENDING", 3: "MAINTENANCE"}.get(hb.get("status"), "UNKNOWN"),
                "time": hb.get("time"),
                "localDateTime": hb.get("localDateTime"),
                "msg": hb.get("msg", ""),
                "ping": hb.get("ping"),
                "important": hb.get("important", False),
                "duration": hb.get("duration"),
                "retries": hb.get("retries", 0),
                "downCount": hb.get("downCount", 0)
            }
            formatted_heartbeats.append(formatted_hb)
        
        return json.dumps(formatted_heartbeats, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении heartbeat данных: {str(e)}"

@tool
def get_uptime_statistics_socketio(monitor_id: int) -> str:
    """
    Получает статистику uptime для монитора через Socket.io API.
    
    Args:
        monitor_id (int): ID монитора
    
    Returns:
        str: JSON строка со статистикой uptime
    """
    try:
        client = get_uptime_kuma_client()
        stats = client.get_uptime_stats(monitor_id)
        
        if not stats:
            return f"❌ Не удалось получить статистику uptime для монитора {monitor_id}"
        
        # Добавляем дополнительную информацию
        monitor = client.get_monitor_by_id(monitor_id)
        monitor_name = monitor.get("name", f"Monitor {monitor_id}") if monitor else f"Monitor {monitor_id}"
        
        result = {
            "monitor_id": monitor_id,
            "monitor_name": monitor_name,
            "statistics": stats,
            "uptime_percentage": stats.get("uptime_percentage", 0),
            "total_checks": stats.get("total_heartbeats", 0),
            "successful_checks": stats.get("up_count", 0),
            "failed_checks": stats.get("down_count", 0)
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении статистики uptime: {str(e)}"

@tool
def get_notifications_socketio() -> str:
    """
    Получает список всех уведомлений из Uptime Kuma через Socket.io API.
    
    Returns:
        str: JSON строка с информацией об уведомлениях
    """
    try:
        client = get_uptime_kuma_client()
        notifications = client.get_notifications()
        
        if not notifications:
            return "❌ Не удалось получить список уведомлений из Uptime Kuma"
        
        # Форматируем уведомления
        formatted_notifications = []
        for notification in notifications:
            formatted_notification = {
                "id": notification.get("id"),
                "name": notification.get("name", "Unknown"),
                "active": notification.get("active", False),
                "isDefault": notification.get("isDefault", False),
                "userID": notification.get("userID"),
                "config": notification.get("config", "{}")
            }
            formatted_notifications.append(formatted_notification)
        
        return json.dumps(formatted_notifications, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении уведомлений: {str(e)}"

@tool
def test_uptime_kuma_socketio_connection() -> str:
    """
    Тестирует подключение к Uptime Kuma через Socket.io API.
    
    Returns:
        str: Результат тестирования Socket.io подключения
    """
    try:
        result = test_uptime_kuma_socketio()
        
        status = "✅ Socket.io подключение работает" if result["connected"] else "❌ Socket.io подключение недоступно"
        auth_status = "✅ Аутентификация успешна" if result["authenticated"] else "❌ Ошибка аутентификации"
        monitors_info = f"Мониторов: {result['monitors_count']}" if result["monitors_count"] > 0 else "Мониторы не найдены"
        notifications_info = f"Уведомлений: {result['notifications_count']}" if result["notifications_count"] > 0 else "Уведомления не найдены"
        
        response = f"""
🔍 **Тест Socket.io подключения к Uptime Kuma**

📊 **Статус подключения**: {status}
🔑 **Аутентификация**: {auth_status}
📈 **Мониторы**: {monitors_info}
🔔 **Уведомления**: {notifications_info}
🌐 **URL**: {client.base_url if 'client' in locals() else 'Не определен'}
"""
        
        if result["error"]:
            response += f"\n❌ **Ошибка**: {result['error']}"
        
        return response
        
    except Exception as e:
        return f"❌ Ошибка при тестировании Socket.io подключения: {str(e)}"

@tool
def get_monitoring_dashboard_data() -> str:
    """
    Получает полные данные для дашборда мониторинга через Socket.io API.
    Включает все мониторы, их статусы, статистику и последние heartbeat'ы.
    
    Returns:
        str: JSON строка с полными данными дашборда
    """
    try:
        client = get_uptime_kuma_client()
        
        # Получаем все данные
        monitors = client.get_monitors()
        notifications = client.get_notifications()
        
        dashboard_data = {
            "summary": {
                "total_monitors": len(monitors),
                "total_notifications": len(notifications),
                "connection_status": client.is_connected()
            },
            "monitors": [],
            "notifications": notifications
        }
        
        # Обрабатываем каждый монитор
        for monitor_id, monitor_data in monitors.items():
            monitor_info = {
                "id": monitor_id,
                "name": monitor_data.get("name", "Unknown"),
                "type": monitor_data.get("type", "Unknown"),
                "url": monitor_data.get("url", "N/A"),
                "active": monitor_data.get("active", False),
                "tags": monitor_data.get("tags", []),
                "recent_heartbeats": client.get_monitor_heartbeats(int(monitor_id), 5),
                "uptime_stats": client.get_uptime_stats(int(monitor_id))
            }
            dashboard_data["monitors"].append(monitor_info)
        
        return json.dumps(dashboard_data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"❌ Ошибка при получении данных дашборда: {str(e)}"

# Список всех Socket.io инструментов для экспорта
# ОТКЛЮЧЕНО: Socket.IO API требует веб-аутентификации
# Согласно официальной документации Uptime Kuma:
# API ключи работают ТОЛЬКО с /metrics endpoint
# Все остальные endpoints (включая Socket.IO) требуют веб-аутентификации
UPTIME_KUMA_SOCKETIO_TOOLS = [
    # Все Socket.IO инструменты отключены
    # Они требуют веб-аутентификации, которая недоступна для API ключей
]
