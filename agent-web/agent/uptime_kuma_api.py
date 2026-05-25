import os
import requests
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class UptimeKumaAPI:
    """Класс для работы с API Uptime Kuma"""
    
    def __init__(self):
        self.base_url = os.getenv("UPTIME_KUMA_URL", "http://localhost:3001")
        self.api_key = os.getenv("UPTIME_KUMA_API")
        self.session = requests.Session()
        
        # Отключаем прокси для Uptime Kuma (он в локальной сети)
        self.session.proxies = {
            'http': None,
            'https': None
        }
        
        # Настройка аутентификации
        if self.api_key:
            # API Key Authentication (HTTP Basic Auth)
            self.session.auth = ("", self.api_key)
        else:
            print("⚠️ UPTIME_KUMA_API не установлен")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Выполняет HTTP запрос к API Uptime Kuma"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Настраиваем аутентификацию через API ключ
            auth = None
            if self.api_key:
                auth = ("", self.api_key)  # HTTP Basic Auth с пустым username
            
            if method.upper() == "GET":
                response = self.session.get(url, auth=auth, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, auth=auth, timeout=10)
            else:
                print(f"❌ Неподдерживаемый HTTP метод: {method}")
                return None
            
            response.raise_for_status()
            
            # Пытаемся распарсить JSON
            try:
                return response.json()
            except json.JSONDecodeError:
                # Если не JSON, возвращаем текст
                return {"content": response.text}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса к Uptime Kuma API: {str(e)}")
            return None
    
    def get_monitors(self) -> Optional[Dict]:
        """Получает список всех мониторов через метрики Prometheus"""
        metrics_data = self._make_request("/metrics")
        if not metrics_data or "content" not in metrics_data:
            return None
        
        # Парсим метрики Prometheus для извлечения информации о мониторах
        monitors = {}
        lines = metrics_data["content"].split('\n')
        
        for line in lines:
            if line.startswith('monitor_status{'):
                # Извлекаем информацию о мониторе из метрики
                # Формат: monitor_status{monitor_name="name",monitor_type="type",...} value
                try:
                    # Парсим имя монитора
                    name_start = line.find('monitor_name="') + 14
                    name_end = line.find('"', name_start)
                    monitor_name = line[name_start:name_end]
                    
                    # Парсим тип монитора
                    type_start = line.find('monitor_type="') + 14
                    type_end = line.find('"', type_start)
                    monitor_type = line[type_start:type_end]
                    
                    # Парсим URL монитора
                    url_start = line.find('monitor_url="') + 13
                    url_end = line.find('"', url_start)
                    monitor_url = line[url_start:url_end]
                    
                    # Парсим статус
                    status_start = line.rfind('} ') + 2
                    status = int(line[status_start:].strip())
                    
                    monitors[monitor_name] = {
                        "name": monitor_name,
                        "type": monitor_type,
                        "url": monitor_url if monitor_url != "https://" else "",
                        "status": status,
                        "status_text": {0: "DOWN", 1: "UP", 2: "PENDING", 3: "MAINTENANCE"}.get(status, "UNKNOWN")
                    }
                except (ValueError, IndexError):
                    continue
        
        return monitors
    
    def get_metrics(self) -> Optional[str]:
        """Получает метрики в формате Prometheus"""
        response = self._make_request("/metrics")
        if response and isinstance(response, dict) and "content" in response:
            return response["content"]
        return None

def get_uptime_kuma_api() -> UptimeKumaAPI:
    """Получает экземпляр API Uptime Kuma"""
    return UptimeKumaAPI()

def test_uptime_kuma_connection() -> Dict[str, Any]:
    """Тестирует подключение к Uptime Kuma API"""
    api = get_uptime_kuma_api()
    
    result = {
        "connected": False,
        "api_available": False,
        "monitors_count": 0,
        "error": None
    }
    
    try:
        # Тестируем базовое подключение через /metrics endpoint
        response = api._make_request("/metrics")
        if response:
            result["connected"] = True
            result["api_available"] = True
            
            # Получаем количество мониторов из метрик
            monitors = api.get_monitors()
            if monitors:
                result["monitors_count"] = len(monitors)
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

if __name__ == "__main__":
    # Тестируем API
    print("🔍 Тестируем подключение к Uptime Kuma API...")
    result = test_uptime_kuma_connection()
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
