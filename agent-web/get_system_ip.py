#!/usr/bin/env python3
"""
Скрипт для автоматического получения IP адреса системы
"""

import socket
import requests
import subprocess
import os

def get_local_ip():
    """Получить локальный IP адрес"""
    try:
        # Пытаемся получить IP через подключение к внешнему сервису
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None

def get_interface_ip():
    """Получить IP адрес основного интерфейса"""
    try:
        # Пытаемся получить IP через ip route
        result = subprocess.run(
            ["ip", "route", "get", "8.8.8.8"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Извлекаем IP из вывода команды
            lines = result.stdout.strip().split()
            for i, word in enumerate(lines):
                if word == "src":
                    return lines[i + 1]
    except Exception:
        pass
    
    return None

def get_external_ip():
    """Получить внешний IP адрес"""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception:
        pass
    
    return None

def main():
    """Основная функция"""
    print("🔍 Определение IP адресов системы...")
    
    # Получаем различные IP адреса
    local_ip = get_local_ip()
    interface_ip = get_interface_ip()
    external_ip = get_external_ip()
    
    print(f"📱 Локальный IP: {local_ip or 'Не определен'}")
    print(f"🌐 IP интерфейса: {interface_ip or 'Не определен'}")
    print(f"🌍 Внешний IP: {external_ip or 'Не определен'}")
    
    # Рекомендуемый IP для homelab
    recommended_ip = local_ip or interface_ip or "your_local_ip"
    print(f"\n💡 Рекомендуемый IP для HOMELAB_HOST: {recommended_ip}")
    
    # Создаем .env файл если его нет
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"\n📝 Создаю файл {env_file}...")
        
        env_content = f"""# ===== Homelab Agent .env =====
# Автоматически сгенерировано скриптом get_system_ip.py

# Основные настройки
TZ=UTC
DEBUG=false
LOG_LEVEL=INFO

# API ключи (заполните реальными значениями)
GIGACHAT_CREDENTIALS=your_gigachat_credentials_here
TAVILY_API_KEY=your_tavily_api_key_here
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here

# Настройки базы данных
AGENT_DB_PASSWORD=your_secure_password_here

# Сетевые настройки
HOMELAB_HOST={recommended_ip}
UPTIME_KUMA_URL=http://{recommended_ip}:3001
AGENT_WEBHOOK_URL=http://{recommended_ip}:8000/api/webhook/uptime-kuma

# VPS настройки
VPS_WEBHOOK_URL=https://your_vps_domain.com/api/uptime-alerts

# Настройки RAG
RAG_DB_DIR=/app/data/index

# Настройки логирования
LOG_FILE=/app/logs/homelab-agent.log
"""
        
        with open(env_file, "w") as f:
            f.write(env_content)
        
        print(f"✅ Файл {env_file} создан с рекомендуемыми настройками")
        print("🔧 Отредактируйте файл и заполните реальные API ключи")
    else:
        print(f"\n📁 Файл {env_file} уже существует")
        print("🔧 Проверьте настройки HOMELAB_HOST в файле")
    
    print(f"\n🚀 Для запуска используйте:")
    print(f"   docker compose up -d")

if __name__ == "__main__":
    main()
