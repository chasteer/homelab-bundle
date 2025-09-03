"""
Модели данных для Homelab Agent
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class LogDoc(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str
    source: str
    content: str
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
