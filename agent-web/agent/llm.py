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
    
    return GigaChat(
        credentials=credentials,
        verify_ssl_certs=False,
        scope="GIGACHAT_API_PERS",
        model="GigaChat-2",
    )

def chat(llm, messages):
    """Выполнение чата с LLM"""
    return llm.invoke(messages)
