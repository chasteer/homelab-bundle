import os
from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat
from groq import Groq

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
        return ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=4096,
            timeout=30
        )
    except Exception as e:
        print(f"❌ Ошибка инициализации Groq: {str(e)}")
        return None

def get_gigachat():
    """Получение экземпляра GigaChat LLM (закомментировано)"""
    # credentials = os.getenv("GIGACHAT_CREDENTIALS")
    # if not credentials:
    #     raise RuntimeError("Не задан GIGACHAT_CREDENTIALS в окружении.")
    
    # try:
    #     return GigaChat(
    #         credentials=credentials,
    #         verify_ssl_certs=False,
    #         scope="GIGACHAT_API_PERS",
    #         model="GigaChat-2",
    #         timeout=30,
    #         max_retries=3
    #     )
    # except Exception as e:
    #     print(f"❌ Ошибка инициализации GigaChat: {str(e)}")
    #     return None
    
    print("⚠️ GigaChat временно отключен, используется Groq")
    return None

def get_llm():
    """Получение LLM (приоритет: Groq -> GigaChat)"""
    # Сначала пробуем Groq
    groq_llm = get_groq()
    if groq_llm:
        print("✅ Используется Groq Llama 3.3 70B Versatile")
        return groq_llm
    
    # Если Groq недоступен, пробуем GigaChat
    gigachat_llm = get_gigachat()
    if gigachat_llm:
        print("✅ Используется GigaChat")
        return gigachat_llm
    
    print("❌ Ни один LLM не доступен")
    return None

def chat(llm, messages):
    """Выполнение чата с LLM"""
    return llm.invoke(messages)
