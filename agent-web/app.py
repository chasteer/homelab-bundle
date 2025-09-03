import os
from fastapi import FastAPI, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlmodel import SQLModel, Field, create_engine, Session, select
from agent.graph import get_graph
from agent.rag import add_docs
from langchain_core.messages import HumanMessage
from formatter import create_enhanced_response
from webhook_uptime import router as uptime_webhook_router
import hmac
import hashlib
import json
import uuid
from datetime import datetime

# Настройки базы данных
DB_TYPE = os.environ.get("DB_TYPE", "postgres")
if DB_TYPE == "postgres":
    DB_PATH = os.environ.get("AGENT_DB", "postgresql://agent:agent123@agent-db:5432/homelab_agent")
else:
    DB_PATH = os.environ.get("AGENT_DB", "sqlite:///./agent.db")

# Создаем движок базы данных
if DB_TYPE == "postgres":
    engine = create_engine(DB_PATH)
else:
    engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

app = FastAPI(title="Homelab Agent Web")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from models import LogDoc

# Создаем таблицы
SQLModel.metadata.create_all(engine)

# Получаем граф агента
GRAPH = get_graph()

# Подключаем вебхук для Uptime Kuma
app.include_router(uptime_webhook_router, prefix="/api", tags=["webhooks"])

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class ChatBody(BaseModel):
    message: str
    compose: Optional[str] = None
    compose_proxy: Optional[str] = None

@app.post("/api/chat")
def chat(body: ChatBody):
    """Обработка чата через агента"""
    try:
        # Создаем уникальный ID сессии
        session_id = str(uuid.uuid4())[:8]
        
        # Запускаем агента
        config = {"configurable": {"thread_id": session_id}}
        result = GRAPH.invoke(
            {"messages": [HumanMessage(body.message)]}, 
            config
        )
        
        # Получаем последнее сообщение от агента
        if result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_content = "Не удалось получить ответ от агента"
        
        # Логируем запрос и ответ
        with Session(engine) as session:
            # Логируем запрос
            request_log = LogDoc(
                kind="chat_request",
                source=session_id,
                content=body.message
            )
            session.add(request_log)
            
            # Логируем ответ
            response_log = LogDoc(
                kind="chat_response", 
                source=session_id,
                content=response_content
            )
            session.add(response_log)
            
            session.commit()
        
        # Возвращаем улучшенный ответ с форматированием
        return create_enhanced_response(response_content, session_id)
        
    except Exception as e:
        # Логируем ошибку
        with Session(engine) as session:
            error_log = LogDoc(
                kind="chat_error",
                source="system",
                content=f"Ошибка в чате: {str(e)}"
            )
            session.add(error_log)
            session.commit()
        
        return {"error": f"Ошибка обработки запроса: {str(e)}"}

@app.post("/api/upload")
async def upload(files: List[UploadFile]):
    """Загрузка файлов для RAG"""
    texts = []
    metas = []
    
    with Session(engine) as session:
        for f in files:
            data = await f.read()
            text = data.decode(errors="ignore")
            doc = LogDoc(
                kind="upload", 
                source=f.filename, 
                content=text
            )
            session.add(doc)
            texts.append(text)
            metas.append({"source": f.filename})
        session.commit()
    
    if texts:
        add_docs(texts, metas)
    
    return {"ok": True, "count": len(texts)}

@app.get("/api/logs")
def get_logs(kind: Optional[str] = None, limit: int = 100):
    """Получение логов"""
    with Session(engine) as session:
        query = select(LogDoc)
        if kind:
            query = query.where(LogDoc.kind == kind)
        query = query.order_by(LogDoc.id.desc()).limit(limit)
        
        logs = session.exec(query).all()
        return [{"id": log.id, "kind": log.kind, "source": log.source, "content": log.content, "timestamp": log.timestamp} for log in logs]

class GitHubWebhookPayload(BaseModel):
    action: str
    pull_request: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None

@app.post("/webhook/github")
async def github_webhook(request: Request, payload: GitHubWebhookPayload):
    """GitHub webhook для автоматического анализа PR"""
    
    # Проверяем подпись webhook (опционально)
    github_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if github_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature.startswith("sha256="):
            raise HTTPException(status_code=401, detail="Invalid signature format")
        
        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            github_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Обрабатываем только открытие/обновление PR
    if payload.action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action {payload.action} not handled"}
    
    if not payload.pull_request or not payload.repository:
        return {"status": "error", "reason": "Missing pull_request or repository data"}
    
    pr = payload.pull_request
    repo = payload.repository
    
    # Извлекаем информацию о PR
    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    pr_number = pr["number"]
    
    # Создаем вопрос для агента
    question = f"анализ кода {owner}/{repo_name} {pr_number}"
    
    # Запускаем анализ через агента
    try:
        session_id = f"github_pr_{owner}_{repo_name}_{pr_number}"
        config = {"configurable": {"thread_id": session_id}}
        
        result = GRAPH.invoke(
            {"messages": [HumanMessage(question)]}, 
            config
        )
        
        # Получаем ответ агента
        if result.get("messages"):
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_content = "Анализ не выполнен"
        
        # Логируем результат
        with Session(engine) as session:
            log_doc = LogDoc(
                kind="webhook",
                source=session_id,
                content=response_content
            )
            session.add(log_doc)
            session.commit()
        
        return {
            "status": "success",
            "pr": f"{owner}/{repo_name}#{pr_number}",
            "analysis_completed": True,
            "response": response_content
        }
        
    except Exception as e:
        # Логируем ошибку
        with Session(engine) as session:
            log_doc = LogDoc(
                kind="webhook_error",
                source=f"github_pr_{owner}_{repo_name}_{pr_number}",
                content=f"Error: {str(e)}"
            )
            session.add(log_doc)
            session.commit()
        
        return {
            "status": "error",
            "pr": f"{owner}/{repo_name}#{pr_number}",
            "error": str(e)
        }

@app.get("/api/health")
def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к базе данных
        with Session(engine) as session:
            session.exec(select(LogDoc).limit(1)).first()
        
        return {
            "status": "healthy", 
            "agent": "available",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/services")
def get_services_status():
    """Получение статуса всех сервисов homelab"""
    try:
        import subprocess
        import json
        
        # Получаем статус Docker контейнеров
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}},{{.Status}},{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        
        services = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 3:
                        services.append({
                            "name": parts[0],
                            "status": parts[1],
                            "ports": parts[2]
                        })
        
        return {
            "services": services,
            "total": len(services),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"Ошибка получения статуса сервисов: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
