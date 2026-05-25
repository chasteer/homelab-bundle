#!/usr/bin/env python3
"""
Простой тест Groq
"""

import requests

def simple_test():
    """Простой тест"""
    
    base_url = "http://192.168.1.200:8000"
    
    print("🚀 Простой тест Groq")
    print("=" * 30)
    
    try:
        response = requests.post(f"{base_url}/api/chat", json={
            "message": "Привет"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успех! Ответ: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    simple_test()
