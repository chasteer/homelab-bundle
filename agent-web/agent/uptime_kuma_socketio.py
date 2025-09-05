import os
import json
import time
import socketio
from typing import Dict, List, Optional, Any, Callable
from dotenv import load_dotenv

load_dotenv()

class UptimeKumaSocketIO:
    """Socket.io клиент для Uptime Kuma API"""
    
    def __init__(self):
        self.base_url = os.getenv("UPTIME_KUMA_URL", "http://uptime-kuma:3001")
        self.username = os.getenv("UPTIME_KUMA_USERNAME", "admin")
        self.password = os.getenv("UPTIME_KUMA_PASSWORD", "admin")
        self.api_key = os.getenv("UPTIME_KUMA_API")
        
        # Создаем Socket.io клиент
        self.sio = socketio.Client()
        self.connected = False
        self.authenticated = False
        self.monitors = {}
        self.notifications = {}
        self.heartbeats = {}
        
        # Настраиваем обработчики событий
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Настраивает обработчики событий Socket.io"""
        
        @self.sio.event
        def connect():
            print("✅ Подключен к Uptime Kuma Socket.io")
            self.connected = True
        
        @self.sio.event
        def disconnect():
            print("❌ Отключен от Uptime Kuma Socket.io")
            self.connected = False
            self.authenticated = False
        
        @self.sio.event
        def connect_error(data):
            print(f"❌ Ошибка подключения к Uptime Kuma: {data}")
        
        @self.sio.event
        def login(data):
            if data.get("ok"):
                print("✅ Успешная аутентификация в Uptime Kuma")
                self.authenticated = True
            else:
                print(f"❌ Ошибка аутентификации: {data.get('msg', 'Неизвестная ошибка')}")
        
        @self.sio.event
        def monitorList(data):
            print(f"📊 Получен список мониторов: {len(data)} мониторов")
            self.monitors = data
        
        @self.sio.event
        def notificationList(data):
            print(f"🔔 Получен список уведомлений: {len(data)} уведомлений")
            self.notifications = data
        
        @self.sio.event
        def heartbeat(data):
            print(f"💓 Получен heartbeat для монитора {data.get('monitorID')}: {data.get('status')}")
            monitor_id = data.get('monitorID')
            if monitor_id not in self.heartbeats:
                self.heartbeats[monitor_id] = []
            self.heartbeats[monitor_id].append(data)
            # Ограничиваем количество heartbeat'ов
            if len(self.heartbeats[monitor_id]) > 100:
                self.heartbeats[monitor_id] = self.heartbeats[monitor_id][-50:]
    
    def connect(self) -> bool:
        """Подключается к Uptime Kuma через Socket.io"""
        try:
            if not self.connected:
                print(f"🔌 Подключаемся к {self.base_url}")
                self.sio.connect(self.base_url)
                
                # Ждем подключения
                timeout = 10
                while not self.connected and timeout > 0:
                    time.sleep(0.1)
                    timeout -= 0.1
                
                if not self.connected:
                    print("❌ Таймаут подключения")
                    return False
                
                # Аутентификация - всегда используем логин/пароль
                print("🔑 Аутентификация через логин/пароль...")
                self.sio.emit('login', {
                    'username': self.username,
                    'password': self.password
                })
                
                # Ждем аутентификации
                timeout = 30  # Увеличиваем таймаут до 30 секунд
                while not self.authenticated and timeout > 0:
                    time.sleep(0.5)
                    timeout -= 0.5
                    if timeout % 5 == 0:  # Каждые 5 секунд выводим статус
                        print(f"⏳ Ожидание аутентификации... {timeout:.1f}s")
                
                if not self.authenticated:
                    print("❌ Таймаут аутентификации")
                    return False
                
                # Запрашиваем данные
                self.sio.emit('getMonitorList')
                self.sio.emit('getNotificationList')
                
                return True
            return True
            
        except Exception as e:
            print(f"❌ Ошибка подключения: {str(e)}")
            return False
    
    def disconnect(self):
        """Отключается от Uptime Kuma"""
        if self.connected:
            self.sio.disconnect()
    
    def get_monitors(self) -> Dict[str, Any]:
        """Получает список мониторов"""
        if not self.connected or not self.authenticated:
            if not self.connect():
                return {}
        
        # Запрашиваем обновленный список
        self.sio.emit('getMonitorList')
        time.sleep(1)  # Ждем получения данных
        
        return self.monitors
    
    def get_monitor_by_id(self, monitor_id: int) -> Optional[Dict[str, Any]]:
        """Получает монитор по ID"""
        monitors = self.get_monitors()
        return monitors.get(str(monitor_id))
    
    def get_monitor_heartbeats(self, monitor_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает heartbeat данные для монитора"""
        if not self.connected or not self.authenticated:
            if not self.connect():
                return []
        
        # Запрашиваем heartbeat данные
        self.sio.emit('getHeartbeatList', {'monitorID': monitor_id, 'limit': limit})
        time.sleep(1)  # Ждем получения данных
        
        return self.heartbeats.get(monitor_id, [])[-limit:]
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Получает список уведомлений"""
        if not self.connected or not self.authenticated:
            if not self.connect():
                return []
        
        # Запрашиваем обновленный список
        self.sio.emit('getNotificationList')
        time.sleep(1)  # Ждем получения данных
        
        return list(self.notifications.values()) if isinstance(self.notifications, dict) else self.notifications
    
    def get_uptime_stats(self, monitor_id: int) -> Dict[str, Any]:
        """Получает статистику uptime для монитора"""
        if not self.connected or not self.authenticated:
            if not self.connect():
                return {}
        
        # Запрашиваем статистику uptime
        self.sio.emit('getUptime', {'monitorID': monitor_id})
        time.sleep(1)  # Ждем получения данных
        
        # Возвращаем базовую статистику
        heartbeats = self.get_monitor_heartbeats(monitor_id, 100)
        if not heartbeats:
            return {}
        
        total_heartbeats = len(heartbeats)
        up_count = sum(1 for hb in heartbeats if hb.get('status') == 1)
        uptime_percentage = (up_count / total_heartbeats * 100) if total_heartbeats > 0 else 0
        
        return {
            'total_heartbeats': total_heartbeats,
            'up_count': up_count,
            'down_count': total_heartbeats - up_count,
            'uptime_percentage': round(uptime_percentage, 2)
        }
    
    def is_connected(self) -> bool:
        """Проверяет статус подключения"""
        return self.connected and self.authenticated

# Глобальный экземпляр клиента
_uptime_kuma_client = None

def get_uptime_kuma_client() -> UptimeKumaSocketIO:
    """Получает глобальный экземпляр клиента Uptime Kuma"""
    global _uptime_kuma_client
    if _uptime_kuma_client is None:
        _uptime_kuma_client = UptimeKumaSocketIO()
    return _uptime_kuma_client

def test_uptime_kuma_socketio() -> Dict[str, Any]:
    """Тестирует подключение к Uptime Kuma через Socket.io"""
    client = get_uptime_kuma_client()
    
    result = {
        "connected": False,
        "authenticated": False,
        "monitors_count": 0,
        "notifications_count": 0,
        "error": None
    }
    
    try:
        if client.connect():
            result["connected"] = True
            result["authenticated"] = client.authenticated
            
            monitors = client.get_monitors()
            if monitors:
                result["monitors_count"] = len(monitors)
            
            notifications = client.get_notifications()
            if notifications:
                result["notifications_count"] = len(notifications)
            
            # Отключаемся после теста
            client.disconnect()
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Тестируем Socket.io клиент
    print("🔍 Тестируем Socket.io подключение к Uptime Kuma...")
    result = test_uptime_kuma_socketio()
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
