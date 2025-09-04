"""
RAG модуль для Homelab Agent
Интегрирован с базой данных логов для контекстного поиска
"""

from typing import List, Dict, Any
import os
import chromadb
from datetime import datetime
from sqlmodel import create_engine, Session, select
from models import LogDoc

# Настройки базы данных
DB_PATH = os.environ.get("AGENT_DB", "sqlite:///./agent.db")
RAG_DB_DIR = os.environ.get("RAG_DB_DIR", "./data/index")
COLLECTION = "homelab_docs"

# Инициализация ChromaDB (отложенная)
client = None
coll = None

def _init_chromadb():
    """Отложенная инициализация ChromaDB"""
    global client, coll
    if client is None:
        try:
            client = chromadb.PersistentClient(path=RAG_DB_DIR)
            if COLLECTION not in [c.name for c in client.list_collections()]:
                coll = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
            else:
                coll = client.get_collection(COLLECTION)
        except Exception as e:
            print(f"Ошибка инициализации ChromaDB: {e}")
            client = None
            coll = None

def add_docs(docs: List[str], metadatas: List[Dict[str, Any]]):
    """Добавление документов в RAG индекс"""
    _init_chromadb()
    if coll is None:
        return []
    try:
        ids = [f"doc_{i}_{abs(hash(d))}" for i, d in enumerate(docs)]
        coll.add(documents=docs, metadatas=metadatas, ids=ids)
        return ids
    except Exception as e:
        print(f"Ошибка добавления документов в RAG: {e}")
        return []

def query(q: str, k: int = 5):
    """Поиск в RAG индексе"""
    try:
        res = coll.query(query_texts=[q], n_results=k)
        items = []
        for i in range(len(res["documents"][0])):
            items.append({
                "document": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "id": res["ids"][0][i]
            })
        return items
    except Exception as e:
        return [{"error": f"Ошибка RAG поиска: {str(e)}"}]

def query_logs(q: str, k: int = 5):
    """Поиск в базе данных логов"""
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        with Session(engine) as session:
            # Простой поиск по содержимому логов
            query_stmt = select(LogDoc).where(LogDoc.content.contains(q))
            logs = session.exec(query_stmt).all()
            
            # Ограничиваем количество результатов
            logs = logs[:k]
            
            items = []
            for log in logs:
                items.append({
                    "document": log.content,
                    "metadata": {
                        "source": log.source,
                        "kind": log.kind,
                        "id": log.id
                    },
                    "id": f"log_{log.id}"
                })
            
            return items
    except Exception as e:
        return [{"error": f"Ошибка поиска в логах: {str(e)}"}]

def add_log_to_rag(log_content: str, log_metadata: Dict[str, Any]):
    """Добавление лога в RAG индекс"""
    try:
        add_docs([log_content], [log_metadata])
        return True
    except Exception as e:
        print(f"Ошибка добавления лога в RAG: {e}")
        return False

def get_recent_context(k: int = 10):
    """Получение недавнего контекста из логов"""
    try:
        # Определяем параметры подключения в зависимости от типа БД
        if DB_PATH.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(DB_PATH, connect_args=connect_args)
        with Session(engine) as session:
            query_stmt = select(LogDoc).order_by(LogDoc.id.desc()).limit(k)
            logs = session.exec(query_stmt).all()
            
            context = []
            for log in logs:
                context.append({
                    "type": log.kind,
                    "source": log.source,
                    "content": log.content[:500] + "..." if len(log.content) > 500 else log.content
                })
            
            return context
    except Exception as e:
        return [{"error": f"Ошибка получения контекста: {str(e)}"}]
