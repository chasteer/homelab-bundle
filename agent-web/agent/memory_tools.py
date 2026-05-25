"""
Инструменты для работы с памятью агента
Позволяют сохранять и извлекать информацию из памяти в рамках сессии
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlmodel import create_engine, Session, select
from models import LogDoc
import os
import json
from datetime import datetime

# Настройки базы данных
DB_TYPE = os.environ.get("DB_TYPE", "postgres")
if DB_TYPE == "postgres":
    DB_PATH = os.environ.get("AGENT_DB") or ""
else:
    DB_PATH = os.environ.get("AGENT_DB", "sqlite:///./agent.db")

# Глобальное хранилище для session_id (временное решение)
_current_session_id = None

def set_session_id(session_id: str):
    """Устанавливает текущий session_id для инструментов памяти"""
    global _current_session_id
    _current_session_id = session_id

def get_session_id() -> str:
    """Получает текущий session_id"""
    return _current_session_id or "default"

@tool
def save_to_memory(key: str, value: str, category: str = "general") -> Dict[str, Any]:
    """
    Сохраняет информацию в память агента для использования в рамках сессии.
    
    Args:
        key: Ключ для сохранения информации (например, "user_preferences", "project_details")
        value: Информация для сохранения
        category: Категория информации (general, preferences, facts, etc.)
    
    Returns:
        Результат сохранения
    """
    session_id = get_session_id()
    
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        
        with Session(engine) as session:
            # Создаем запись в памяти
            memory_entry = LogDoc(
                kind="memory",
                source=f"{session_id}_{category}",
                content=json.dumps({
                    "key": key,
                    "value": value,
                    "category": category,
                    "timestamp": datetime.now().isoformat()
                })
            )
            session.add(memory_entry)
            session.commit()
            
            return {
                "success": True,
                "message": f"✅ Информация '{key}' успешно сохранена в память",
                "key": key,
                "category": category,
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Ошибка сохранения в память: {str(e)}",
            "error": str(e)
        }

@tool
def get_from_memory(key: str, category: str = "general") -> Dict[str, Any]:
    """
    Извлекает информацию из памяти агента по ключу.
    
    Args:
        key: Ключ для поиска информации
        category: Категория информации для поиска
    
    Returns:
        Найденная информация или сообщение об отсутствии
    """
    session_id = get_session_id()
    
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        
        with Session(engine) as session:
            # Ищем записи в памяти
            query_stmt = select(LogDoc).where(
                LogDoc.kind == "memory",
                LogDoc.source == f"{session_id}_{category}"
            ).order_by(LogDoc.id.desc())
            
            memory_entries = session.exec(query_stmt).all()
            
            # Ищем нужный ключ
            for entry in memory_entries:
                try:
                    data = json.loads(entry.content)
                    if data.get("key") == key:
                        return {
                            "success": True,
                            "found": True,
                            "key": key,
                            "value": data.get("value"),
                            "category": data.get("category"),
                            "timestamp": data.get("timestamp"),
                            "message": f"✅ Найдена информация: {data.get('value')}"
                        }
                except json.JSONDecodeError:
                    continue
            
            return {
                "success": True,
                "found": False,
                "message": f"❌ Информация с ключом '{key}' не найдена в памяти",
                "key": key,
                "category": category
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Ошибка извлечения из памяти: {str(e)}",
            "error": str(e)
        }

@tool
def list_memory_keys(category: str = "general") -> Dict[str, Any]:
    """
    Показывает все ключи, сохраненные в памяти агента для данной сессии.
    
    Args:
        category: Категория информации (опционально)
    
    Returns:
        Список всех сохраненных ключей
    """
    session_id = get_session_id()
    
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        
        with Session(engine) as session:
            # Ищем записи в памяти
            query_stmt = select(LogDoc).where(
                LogDoc.kind == "memory",
                LogDoc.source == f"{session_id}_{category}"
            ).order_by(LogDoc.id.desc())
            
            memory_entries = session.exec(query_stmt).all()
            
            keys = []
            for entry in memory_entries:
                try:
                    data = json.loads(entry.content)
                    keys.append({
                        "key": data.get("key"),
                        "category": data.get("category"),
                        "timestamp": data.get("timestamp")
                    })
                except json.JSONDecodeError:
                    continue
            
            return {
                "success": True,
                "keys": keys,
                "count": len(keys),
                "session_id": session_id,
                "category": category,
                "message": f"📋 Найдено {len(keys)} ключей в памяти"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Ошибка получения списка ключей: {str(e)}",
            "error": str(e)
        }

@tool
def get_conversation_history(limit: int = 10) -> Dict[str, Any]:
    """
    Получает историю разговора для данной сессии.
    
    Args:
        limit: Максимальное количество сообщений для получения
    
    Returns:
        История разговора
    """
    session_id = get_session_id()
    
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        
        with Session(engine) as session:
            # Ищем записи чата для данной сессии
            query_stmt = select(LogDoc).where(
                LogDoc.source == session_id,
                LogDoc.kind.in_(["chat_request", "chat_response"])
            ).order_by(LogDoc.id.desc()).limit(limit * 2)  # Умножаем на 2, так как у нас запрос + ответ
            
            chat_entries = session.exec(query_stmt).all()
            
            # Группируем запросы и ответы
            history = []
            for entry in chat_entries:
                history.append({
                    "type": entry.kind,
                    "content": entry.content,
                    "timestamp": entry.timestamp
                })
            
            # Сортируем по времени (от старых к новым)
            history.sort(key=lambda x: x["timestamp"])
            
            return {
                "success": True,
                "history": history,
                "count": len(history),
                "session_id": session_id,
                "message": f"📜 История разговора: {len(history)} сообщений"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Ошибка получения истории разговора: {str(e)}",
            "error": str(e)
        }

@tool
def remember_user_preference(preference: str, value: str) -> Dict[str, Any]:
    """
    Запоминает предпочтения пользователя для использования в будущих разговорах.
    
    Args:
        preference: Название предпочтения (например, "language", "timezone", "name")
        value: Значение предпочтения
    
    Returns:
        Результат сохранения предпочтения
    """
    return save_to_memory(preference, value, "preferences")

@tool
def get_user_preference(preference: str) -> Dict[str, Any]:
    """
    Получает сохраненное предпочтение пользователя.
    
    Args:
        preference: Название предпочтения
    
    Returns:
        Сохраненное предпочтение или сообщение об отсутствии
    """
    return get_from_memory(preference, "preferences")

# Список всех инструментов памяти
MEMORY_TOOLS = [
    save_to_memory,
    get_from_memory,
    list_memory_keys,
    get_conversation_history,
    remember_user_preference,
    get_user_preference
]