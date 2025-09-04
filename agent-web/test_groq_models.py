#!/usr/bin/env python3
"""
Тест доступных моделей Groq через прокси
"""

import os
from groq import Groq

def test_groq_models():
    print("🔍 Проверяем доступные модели Groq через прокси...")
    
    # Настройка прокси
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        print(f"🌐 Используется прокси: {proxy_url}")
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY не установлен")
        return
    
    try:
        # Инициализация Groq клиента
        client = Groq(api_key=api_key)
        
        # Получение списка моделей
        print("📋 Получаем список моделей...")
        models = client.models.list()
        
        print(f"✅ Найдено моделей: {len(models.data)}")
        for model in models.data:
            print(f"  - {model.id}")
            
        # Тестируем доступные модели
        available_models = [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant", 
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768"
        ]
        
        print("\n🧪 Тестируем доступные модели...")
        for model_name in available_models:
            try:
                print(f"  Тестируем {model_name}...")
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Привет! Ответь коротко."}],
                    max_tokens=10
                )
                print(f"  ✅ {model_name} - работает!")
                print(f"     Ответ: {response.choices[0].message.content}")
                break
            except Exception as e:
                print(f"  ❌ {model_name} - ошибка: {str(e)[:100]}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_groq_models()
