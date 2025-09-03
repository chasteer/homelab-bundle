#!/usr/bin/env python3
"""
Автоматическая настройка вебхука Uptime Kuma для Homelab Agent
"""

import os
import requests
import json
import time
import subprocess

# Получаем настройки из переменных окружения
KUMA_URL = os.environ.get("UPTIME_KUMA_URL", "http://192.168.1.200:3001")
AGENT_WEBHOOK_URL = os.environ.get("AGENT_WEBHOOK_URL", "http://192.168.1.200:8000/api/webhook/uptime-kuma")

def get_agent_internal_ip():
    """Получаем внутренний IP агента в Docker сети"""
    try:
        result = subprocess.run([
            "sudo", "docker", "inspect", "homelab-agent", 
            "--format", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"
        ], capture_output=True, text=True, check=True)
        
        internal_ip = result.stdout.strip()
        if internal_ip:
            return internal_ip
    except Exception as e:
        print(f"⚠️  Не удалось получить внутренний IP агента: {e}")
    
    return "172.20.0.11"  # Fallback IP

def check_kuma_access():
    """Проверяем доступность Uptime Kuma"""
    try:
        response = requests.get(f"{KUMA_URL}/api/status", timeout=10)
        if response.status_code == 200:
            print(f"✅ Uptime Kuma доступен: {KUMA_URL}")
            return True
        else:
            print(f"❌ Uptime Kuma недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к Uptime Kuma: {e}")
        return False

def check_agent_webhook():
    """Проверяем доступность вебхука агента"""
    try:
        response = requests.get(f"{AGENT_WEBHOOK_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Вебхук агента доступен: {AGENT_WEBHOOK_URL}")
            return True
        else:
            print(f"❌ Вебхук агента недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к вебхуку агента: {e}")
        return False

def check_docker_network_connectivity():
    """Проверяем сетевое подключение между контейнерами"""
    agent_ip = get_agent_internal_ip()
    print(f"\n🔍 Проверка сетевого подключения:")
    print(f"   Агент внутренний IP: {agent_ip}")
    
    try:
        # Проверяем, может ли Uptime Kuma подключиться к агенту
        result = subprocess.run([
            "sudo", "docker", "exec", "uptime-kuma", 
            "curl", "-s", "--connect-timeout", "5", 
            f"http://{agent_ip}:8000/api/webhook/uptime-kuma/health"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Uptime Kuma может подключиться к агенту по {agent_ip}")
            return True, agent_ip
        else:
            print(f"❌ Uptime Kuma НЕ может подключиться к агенту по {agent_ip}")
            return False, agent_ip
    except Exception as e:
        print(f"❌ Ошибка проверки сетевого подключения: {e}")
        return False, agent_ip

def create_webhook_config(agent_internal_ip):
    """Создает конфигурацию вебхука для Uptime Kuma"""
    webhook_config = {
        "name": "Homelab Agent Webhook",
        "type": "webhook",
        "url": f"http://{agent_internal_ip}:8000/api/webhook/uptime-kuma",
        "method": "POST",
        "contentType": "application/json",
        "retry": 3,
        "retryInterval": 60,
        "events": ["up", "down", "paused", "maintenance"],
        "isDefault": False,
        "applyExisting": True
    }
    
    print(f"\n📋 Конфигурация вебхука:")
    print(json.dumps(webhook_config, indent=2, ensure_ascii=False))
    return webhook_config

def main():
    """Основная функция"""
    print("🔧 Автоматическая настройка вебхука Uptime Kuma")
    print("=" * 50)
    
    # Проверяем доступность сервисов
    if not check_kuma_access():
        print("\n❌ Невозможно продолжить - Uptime Kuma недоступен")
        return
    
    if not check_agent_webhook():
        print("\n❌ Невозможно продолжить - вебхук агента недоступен")
        return
    
    # Проверяем сетевое подключение
    network_ok, agent_ip = check_docker_network_connectivity()
    
    if not network_ok:
        print(f"\n⚠️  ВНИМАНИЕ: Сетевое подключение между контейнерами не работает!")
        print(f"   Это может быть причиной, почему уведомления не приходят.")
    
    # Создаем конфигурацию
    webhook_config = create_webhook_config(agent_ip)
    
    print(f"\n📝 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:")
    print("=" * 50)
    print("1. Откройте Uptime Kuma в браузере:")
    print(f"   {KUMA_URL}")
    print("\n2. Войдите в систему (создайте аккаунт если нужно)")
    print("\n3. Перейдите в Settings → Notifications")
    print("\n4. Нажмите 'Add New Notification'")
    print("\n5. Выберите тип 'Webhook'")
    print("\n6. Заполните поля:")
    print(f"   - Name: Homelab Agent Webhook")
    print(f"   - URL: http://{agent_ip}:8000/api/webhook/uptime-kuma ⭐")
    print(f"   - Method: POST")
    print(f"   - Content Type: application/json")
    print(f"   - Events: выберите все (up, down, paused, maintenance)")
    
    if not network_ok:
        print(f"\n⚠️  ВАЖНО: Используйте внутренний IP {agent_ip}, а не внешний!")
        print(f"   Внешний IP 192.168.1.200 недоступен из контейнеров Docker.")
    
    print("\n7. Нажмите 'Test' для проверки")
    print("8. Нажмите 'Save' для сохранения")
    
    print(f"\n🔍 ПРОВЕРКА НАСТРОЙКИ:")
    print("=" * 50)
    print("После настройки вебхука:")
    print("1. Остановите любой сервис (например, TorrServer)")
    print("2. Подождите несколько секунд")
    print("3. Проверьте логи агента:")
    print("   sudo docker logs homelab-agent | grep webhook")
    print("4. Запустите сервис обратно")
    print("5. Проверьте логи снова")
    
    print(f"\n📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
    print("=" * 50)
    print("• Документация: UPTIME_KUMA_INTEGRATION.md")
    print("• Правильная конфигурация: WEBHOOK_CORRECT_CONFIG.md")
    print("• Пошаговая настройка: WEBHOOK_SETUP_STEPS.md")
    print("• Устранение неполадок: README_SECURITY_UPDATE.md")

if __name__ == "__main__":
    main()
