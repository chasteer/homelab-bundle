import os
from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat

# Загружаем переменные окружения
load_dotenv()

def get_gigachat():
    """Получение экземпляра GigaChat LLM"""
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    if not credentials:
        raise RuntimeError("Не задан GIGACHAT_CREDENTIALS в окружении.")
    
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
        # Возвращаем заглушку для тестирования
        return None

def chat(llm, messages):
    """Выполнение чата с LLM"""
    return llm.invoke(messages)
