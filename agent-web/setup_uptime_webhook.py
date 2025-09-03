#!/usr/bin/env python3
"""
Скрипт для настройки вебхука Uptime Kuma
"""

import requests
import json
import time

# Получаем URL из переменных окружения
KUMA_URL = os.environ.get("UPTIME_KUMA_URL", "http://your_local_ip:3001")
AGENT_WEBHOOK_URL = os.environ.get("AGENT_WEBHOOK_URL", "http://your_local_ip:8000/api/webhook/uptime-kuma")

def setup_webhook():
    """Настройка вебхука в Uptime Kuma"""
    
    print("🚀 Настройка вебхука Uptime Kuma для Homelab Agent...")
    
    # Проверяем доступность Uptime Kuma
    try:
        response = requests.get(f"{KUMA_URL}/api/monitor", timeout=10)
        if response.status_code != 200:
            print(f"❌ Uptime Kuma недоступен: {response.status_code}")
            return False
        print("✅ Uptime Kuma доступен")
    except Exception as e:
        print(f"❌ Ошибка подключения к Uptime Kuma: {e}")
        return False
    
    # Проверяем доступность агента
    try:
        response = requests.get(f"{AGENT_WEBHOOK_URL}/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ Агент недоступен: {response.status_code}")
            return False
        print("✅ Homelab Agent доступен")
    except Exception as e:
        print(f"❌ Ошибка подключения к агенту: {e}")
        return False
    
    print("\n📋 Инструкция по настройке:")
    print("1. Откройте Uptime Kuma: http://your_local_ip:3001")
    print("2. Перейдите в Settings → Notifications")
    print("3. Нажмите 'Add New Notification'")
    print("4. Настройте:")
    print(f"   - Type: Webhook")
    print(f"   - Name: Homelab Agent Webhook")
    print(f"   - URL: {AGENT_WEBHOOK_URL}")
    print(f"   - Method: POST")
    print(f"   - Content Type: application/json")
    print("5. В триггерах выберите:")
    print("   - When monitor goes down: ✅")
    print("   - When monitor goes up: ✅ (опционально)")
    print("6. Сохраните и протестируйте")
    
    return True

if __name__ == "__main__":
    setup_webhook()
