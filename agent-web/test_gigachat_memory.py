#!/usr/bin/env python3
import requests
import json

def test_agent_memory():
    base_url = "http://192.168.1.200:8000"
    
    print("🧪 Тестируем агента с GigaChat и памятью...")
    
    # Тест 1: Сохранение информации
    print("\n1️⃣ Сохраняем информацию о пользователе...")
    response1 = requests.post(f"{base_url}/api/chat", json={
        "message": "Меня зовут Алексей, мне 30 лет, я программист. Запомни это.",
        "session_id": "test_session_123"
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✅ Ответ: {result1['response']}")
        print(f"📝 Session ID: {result1.get('session_id', 'N/A')}")
    else:
        print(f"❌ Ошибка: {response1.status_code}")
        return
    
    # Тест 2: Получение сохраненной информации
    print("\n2️⃣ Проверяем, что агент помнит информацию...")
    response2 = requests.post(f"{base_url}/api/chat", json={
        "message": "Как меня зовут?",
        "session_id": "test_session_123"
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✅ Ответ: {result2['response']}")
    else:
        print(f"❌ Ошибка: {response2.status_code}")
    
    # Тест 3: Проверка предпочтений
    print("\n3️⃣ Проверяем предпочтения...")
    response3 = requests.post(f"{base_url}/api/chat", json={
        "message": "Что ты помнишь обо мне?",
        "session_id": "test_session_123"
    })
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"✅ Ответ: {result3['response']}")
    else:
        print(f"❌ Ошибка: {response3.status_code}")

if __name__ == "__main__":
    test_agent_memory()
