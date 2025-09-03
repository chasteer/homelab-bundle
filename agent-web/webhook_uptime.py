"""
Вебхук для получения уведомлений от Uptime Kuma
"""

import os
import json
import requests
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union

router = APIRouter()

class UptimeAlert(BaseModel):
    """Модель уведомления от Uptime Kuma"""
    monitorID: Optional[int] = None
    monitorURL: Optional[str] = None
    monitorName: Optional[str] = None
    monitorStatus: Optional[int] = None  # 0=down, 1=up, 2=maintenance
    alertType: Optional[str] = None
    alertMessage: Optional[str] = None
    alertDateTime: Optional[str] = None
    monitorType: Optional[str] = None
    monitorHostname: Optional[str] = None
    monitorPort: Optional[int] = None
    
    # Дополнительные поля для тестовых сообщений
    heartbeat: Optional[Any] = None
    monitor: Optional[Any] = None
    msg: Optional[str] = None

@router.post("/webhook/uptime-kuma")
async def uptime_kuma_webhook(alert: UptimeAlert):
    """Обработка вебхука от Uptime Kuma"""
    try:
        # Проверяем, это тестовое сообщение или реальное уведомление
        if alert.msg and "Testing" in alert.msg:
            # Это тестовое сообщение от Uptime Kuma
            print(f"🧪 Получено тестовое сообщение от Uptime Kuma: {alert.msg}")
            
            return {
                "success": True,
                "message": "Тестовое сообщение получено",
                "test_message": alert.msg,
                "timestamp": datetime.now().isoformat()
            }
        
        # Это реальное уведомление
        if not alert.monitorName:
            # Если нет имени монитора, используем сообщение или создаем дефолтное
            monitor_name = alert.msg or "Unknown Monitor"
        else:
            monitor_name = alert.monitorName
            
        if not alert.alertMessage:
            # Если нет сообщения, создаем дефолтное
            alert_message = f"Status changed to {alert.monitorStatus}" if alert.monitorStatus is not None else "Status changed"
        else:
            alert_message = alert.alertMessage
        
        # Логируем уведомление
        print(f"🚨 Получено уведомление от Uptime Kuma: {monitor_name} - {alert_message}")
        
        # Определяем статус
        status_map = {0: "down", 1: "up", 2: "maintenance"}
        status = status_map.get(alert.monitorStatus, "unknown") if alert.monitorStatus is not None else "unknown"
        
        # Формируем детали для агента
        details = {
            "monitor_name": monitor_name,
            "monitor_url": alert.monitorURL or "N/A",
            "status": status,
            "alert_type": alert.alertType or "status_change",
            "message": alert_message,
            "datetime": alert.alertDateTime or datetime.now().isoformat(),
            "monitor_type": alert.monitorType or "unknown",
            "hostname": alert.monitorHostname,
            "port": alert.monitorPort
        }
        
        # Отправляем уведомление на VPS
        vps_response = await send_to_vps(monitor_name, status, details)
        
        # Возвращаем результат
        return {
            "success": True,
            "message": "Уведомление обработано",
            "vps_response": vps_response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка обработки вебхука: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

async def send_to_vps(service_name: str, status: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Отправка уведомления на VPS"""
    try:
        # Данные для отправки
        alert_data = {
            "source": "homelab_uptime_kuma",
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "status": status,
            "details": details,
            "host": os.environ.get("HOMELAB_HOST", "localhost"),
            "webhook_type": "uptime_kuma"
        }
        
        # Отправляем на VPS
        vps_url = os.environ.get("VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts")
        
        response = requests.post(
            vps_url,
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"success": True, "message": "Отправлено на VPS"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/webhook/uptime-kuma/health")
async def webhook_health():
    """Проверка здоровья вебхука"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "uptime-kuma-webhook"
    }
