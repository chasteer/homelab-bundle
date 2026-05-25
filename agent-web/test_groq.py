#!/usr/bin/env python3
"""
Тест Groq
"""

import requests
import time

def test_groq():
    """Тест Groq"""
    
    base_url = "http://192.168.1.200:8000"
    
    print("🚀 Тест Groq")
    print("=" * 30)
    
    # Простой тест
    print("\n1️⃣ Простой запрос...")
    try:
        response = requests.post(f"{base_url}/api/chat", json={
            "message": "Привет! Как дела?"
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"✅ Session ID: {session_id}")
            print(f"Ответ: {data.get('response', '')[:200]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    time.sleep(2)
    
    # Тест памяти
    print("\n2️⃣ Тест памяти...")
    try:
        response = requests.post(f"{base_url}/api/chat", json={
            "message": "Запомни, что меня зовут Иван",
            "session_id": session_id
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ответ: {data.get('response', '')[:150]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    time.sleep(2)
    
    # Тест извлечения памяти
    print("\n3️⃣ Тест извлечения памяти...")
    try:
        response = requests.post(f"{base_url}/api/chat", json={
            "message": "Как меня зовут?",
            "session_id": session_id
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ответ: {data.get('response', '')[:150]}...")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    test_groq()
