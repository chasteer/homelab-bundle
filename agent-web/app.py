"""
Homelab Incident Service — вебхуки Uptime Kuma, GitHub (опционально), health API.
Чат-интерфейс удалён; анализ падений — через Cursor CLI.
"""

import os
import hmac
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine, Session, select

from webhook_uptime import router as uptime_webhook_router
from agent.cursor_incident import check_cursor_cli_available
from models import LogDoc

DB_TYPE = os.environ.get("DB_TYPE", "postgres")
if DB_TYPE == "postgres":
    DB_PATH = os.environ.get("AGENT_DB")
    if not DB_PATH:
        raise RuntimeError(
            "AGENT_DB не задан. Задайте в .env или docker-compose (см. env.example)."
        )
else:
    DB_PATH = os.environ.get("AGENT_DB", "sqlite:///./agent.db")

if DB_TYPE == "postgres":
    engine = create_engine(DB_PATH)
else:
    engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

app = FastAPI(title="Homelab Incident Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLModel.metadata.create_all(engine)
app.include_router(uptime_webhook_router, prefix="/api", tags=["webhooks"])


@app.get("/")
def root():
    return {
        "service": "homelab-incident-service",
        "endpoints": {
            "health": "/api/health",
            "uptime_webhook": "/api/webhook/uptime-kuma",
            "uptime_webhook_health": "/api/webhook/uptime-kuma/health",
            "test_cursor": "/api/webhook/uptime-kuma/test-cursor",
        },
    }


@app.get("/api/health")
def health_check():
    cursor = check_cursor_cli_available()
    db_error = None
    try:
        with Session(engine) as session:
            session.exec(select(LogDoc).limit(1)).first()
        db_ok = True
    except Exception as e:
        db_ok = False
        db_error = str(e)

    healthy = db_ok and cursor.get("cursor_cli_available") and cursor.get("cursor_api_key_set")
    payload = {
        "status": "healthy" if healthy else "degraded",
        "database": "connected" if db_ok else "error",
        "cursor_incidents_dir": os.environ.get("CURSOR_INCIDENTS_DIR", "/app/logs/incidents"),
        "timestamp": datetime.now().isoformat(),
        **cursor,
    }
    if db_error:
        payload["database_error"] = db_error
    return payload


@app.get("/api/logs")
def get_logs(kind: Optional[str] = None, limit: int = 100):
    with Session(engine) as session:
        query = select(LogDoc)
        if kind:
            query = query.where(LogDoc.kind == kind)
        query = query.order_by(LogDoc.id.desc()).limit(limit)
        logs = session.exec(query).all()
        return [
            {
                "id": log.id,
                "kind": log.kind,
                "source": log.source,
                "content": log.content[:500] if log.content else "",
                "timestamp": log.timestamp,
            }
            for log in logs
        ]


@app.get("/api/services")
def get_services_status():
    try:
        import subprocess

        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}},{{.Status}},{{.Ports}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        services = []
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split(",")
                    if len(parts) >= 3:
                        services.append(
                            {
                                "name": parts[0],
                                "status": parts[1],
                                "ports": parts[2],
                            }
                        )
        return {
            "services": services,
            "total": len(services),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


class GitHubWebhookPayload(BaseModel):
    action: str
    pull_request: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None


@app.post("/webhook/github")
async def github_webhook(request: Request, payload: GitHubWebhookPayload):
    """GitHub webhook — логирование; анализ PR через Cursor отдельно при необходимости."""
    github_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if github_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not signature.startswith("sha256="):
            raise HTTPException(status_code=401, detail="Invalid signature format")
        body = await request.body()
        expected = "sha256=" + hmac.new(
            github_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if payload.action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action {payload.action} not handled"}

    if not payload.pull_request or not payload.repository:
        return {"status": "error", "reason": "Missing pull_request or repository data"}

    pr = payload.pull_request
    repo = payload.repository
    owner = repo["owner"]["login"]
    repo_name = repo["name"]
    pr_number = pr["number"]
    session_id = f"github_pr_{owner}_{repo_name}_{pr_number}"

    with Session(engine) as session:
        log_doc = LogDoc(
            kind="webhook",
            source=session_id,
            content=f"GitHub PR #{pr_number} {payload.action} — чат-агент отключён",
        )
        session.add(log_doc)
        session.commit()

    return {
        "status": "logged",
        "pr": f"{owner}/{repo_name}#{pr_number}",
        "note": "PR analysis via chat removed; use Cursor IDE or extend cursor_incident if needed",
    }
