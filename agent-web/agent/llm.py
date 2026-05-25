import os
from dotenv import load_dotenv
from groq import Groq
import random

# Импорт GigaChat только если доступен
try:
    from langchain_gigachat.chat_models import GigaChat
    GIGACHAT_AVAILABLE = True
except ImportError:
    GigaChat = None
    GIGACHAT_AVAILABLE = False

# Загружаем переменные окружения
load_dotenv()

# Список доступных моделей Groq (в порядке приоритета)
GROQ_MODELS = [
    "qwen/qwen3-32b",           # Основная модель - стабильная
    "llama-3.1-8b-instant",     # Быстрая модель
    "llama-3.3-70b-versatile",  # Большая модель с хорошим контекстом
    "openai/gpt-oss-120b",      # Большая модель OpenAI
    "deepseek-r1-distill-llama-70b",  # DeepSeek (может быть перегружена)
]

def get_random_groq_model():
    """Получить случайную модель из списка доступных"""
    return random.choice(GROQ_MODELS)

def get_next_groq_model(current_model=None):
    """Получить следующую модель в списке"""
    if current_model in GROQ_MODELS:
        current_index = GROQ_MODELS.index(current_model)
        next_index = (current_index + 1) % len(GROQ_MODELS)
        return GROQ_MODELS[next_index]
    else:
        return GROQ_MODELS[0]  # Возвращаем первую модель по умолчанию

def get_groq(model_name=None, retry_count=0):
    """Получение экземпляра Groq LLM с поддержкой переключения моделей"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ Не задан GROQ_API_KEY в окружении.")
        return None
    
    try:
        from langchain_groq import ChatGroq
        
        # Настройки прокси (можно отключить для Groq)
        use_proxy = os.getenv("GROQ_USE_PROXY", "true").lower() == "true"
        proxy_url = os.getenv("PROXY_URL")
        
        if use_proxy and proxy_url:
            print(f"🌐 Используется прокси для Groq: {proxy_url}")
            # НЕ устанавливаем глобальные переменные прокси, чтобы не влиять на другие HTTP запросы
        else:
            print("🚫 Прокси отключен для Groq")
        
        # Выбираем модель
        if model_name is None:
            model_name = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
        
        print(f"🤖 Используется модель Groq: {model_name}")
        
        # Настройки прокси для Groq
        groq_kwargs = {
            "groq_api_key": api_key,
            "model_name": model_name,
            "temperature": 0.1,
            "max_tokens": 2048,  # Уменьшаем для скорости
            "timeout": 60,  # Увеличиваем таймаут
            "max_retries": 3
        }
        
        # Добавляем прокси только если нужно
        if use_proxy and proxy_url:
            groq_kwargs["http_client"] = {
                "proxies": {
                    "http": proxy_url,
                    "https": proxy_url
                }
            }
        
        return ChatGroq(**groq_kwargs)
    except Exception as e:
        print(f"❌ Ошибка инициализации Groq: {str(e)}")
        return None

def get_groq_with_fallback(current_model=None):
    """Получить Groq LLM с автоматическим переключением моделей при ошибках"""
    # Если не указана текущая модель, используем из окружения
    if current_model is None:
        current_model = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
    
    # Пробуем текущую модель
    llm = get_groq(current_model)
    if llm is not None:
        return llm, current_model
    
    # Если текущая модель не работает, пробуем другие
    print(f"🔄 Модель {current_model} недоступна, пробуем другие...")
    
    for model in GROQ_MODELS:
        if model != current_model:
            print(f"🔄 Пробуем модель: {model}")
            llm = get_groq(model)
            if llm is not None:
                print(f"✅ Переключились на модель: {model}")
                return llm, model
    
    print("❌ Все модели Groq недоступны")
    return None, None

def get_gigachat():
    """Получение экземпляра GigaChat LLM"""
    if not GIGACHAT_AVAILABLE:
        print("⚠️ GigaChat недоступен (модуль не установлен)")
        return None
    
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        print("⚠️ GIGACHAT_CREDENTIALS не установлен")
        return None
    
    try:
        return GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-2",
            timeout=30,
            max_retries=3
        )
    except Exception as e:
        print(f"❌ Ошибка инициализации GigaChat: {str(e)}")
        return None

def get_openai():
    """Получение экземпляра OpenAI LLM"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY не установлен")
        return None
    
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            openai_api_key=api_key,
            model_name="gpt-4o-mini",
            temperature=0.1,
            max_tokens=4096,
            timeout=30
        )
    except Exception as e:
        print(f"❌ Ошибка инициализации OpenAI: {str(e)}")
        return None

def get_llm():
    """Получение LLM (приоритет определяется переменной окружения PREFERRED_LLM)"""
    preferred_llm = os.getenv("PREFERRED_LLM", "gigachat").lower()
    
    if preferred_llm == "groq":
        # Пробуем Groq с автоматическим переключением моделей
        groq_llm, model_name = get_groq_with_fallback()
        if groq_llm:
            print("✅ Используется Groq")
            return groq_llm
        print("⚠️ Все модели Groq недоступны, переключаемся на GigaChat")
    
    if preferred_llm in ["gigachat", "giga"]:
        # Пробуем GigaChat
        gigachat_llm = get_gigachat()
        if gigachat_llm:
            print("✅ Используется GigaChat")
            return gigachat_llm
        print("⚠️ GigaChat недоступен, переключаемся на Groq")
    
    if preferred_llm == "openai":
        # Пробуем OpenAI
        openai_llm = get_openai()
        if openai_llm:
            print("✅ Используется OpenAI GPT-4o-mini")
            return openai_llm
        print("⚠️ OpenAI недоступен, переключаемся на GigaChat")
    
    # Fallback: пробуем все доступные LLM
    print("🔄 Пробуем все доступные LLM...")
    
    # GigaChat
    gigachat_llm = get_gigachat()
    if gigachat_llm:
        print("✅ Используется GigaChat (fallback)")
        return gigachat_llm
    
    # Groq
    groq_llm = get_groq()
    if groq_llm:
        print("✅ Используется Groq (fallback)")
        return groq_llm
    
    # OpenAI
    openai_llm = get_openai()
    if openai_llm:
        print("✅ Используется OpenAI (fallback)")
        return openai_llm
    
    print("❌ Ни один LLM не доступен")
    print("💡 Рекомендации:")
    print("   1. Проверьте GROQ_API_KEY в .env файле")
    print("   2. Проверьте OPENAI_API_KEY в .env файле")
    print("   3. Проверьте GIGACHAT_CREDENTIALS в .env файле")
    print("   4. Убедитесь, что API ключи действительны")
    return None

def chat(llm, messages):
    """Выполнение чата с LLM"""
    return llm.invoke(messages)