import os
from dotenv import load_dotenv
from groq import Groq

# Импорт GigaChat только если доступен
try:
    from langchain_gigachat.chat_models import GigaChat
    GIGACHAT_AVAILABLE = True
except ImportError:
    GigaChat = None
    GIGACHAT_AVAILABLE = False

# Загружаем переменные окружения
load_dotenv()

def get_groq():
    """Получение экземпляра Groq LLM"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ Не задан GROQ_API_KEY в окружении.")
        return None
    
    try:
        from langchain_groq import ChatGroq
        
        # Настройки прокси
        proxy_url = os.getenv("PROXY_URL")
        if proxy_url:
            print(f"🌐 Используется прокси: {proxy_url}")
            # Устанавливаем переменные окружения для прокси
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
        
        return ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=4096,
            timeout=30
        )
    except Exception as e:
        print(f"❌ Ошибка инициализации Groq: {str(e)}")
        return None

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
    """Получение LLM (приоритет: Groq -> OpenAI -> GigaChat)"""
    # Сначала пробуем Groq
    groq_llm = get_groq()
    if groq_llm:
        print("✅ Используется Groq Llama 3.1 8B Instant")
        return groq_llm
    
    # Если Groq недоступен, пробуем OpenAI
    openai_llm = get_openai()
    if openai_llm:
        print("✅ Используется OpenAI GPT-4o-mini")
        return openai_llm
    
    # Если OpenAI недоступен, пробуем GigaChat
    gigachat_llm = get_gigachat()
    if gigachat_llm:
        print("✅ Используется GigaChat")
        return gigachat_llm
    
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