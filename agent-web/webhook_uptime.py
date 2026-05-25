"""
Вебхук Uptime Kuma: анализ инцидента через Cursor CLI → уведомление на VPS → Telegram.
"""

import os
import json
import requests
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from agent.cursor_incident import generate_cursor_incident_analysis

try:
    from agent.rag import add_log_to_rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

router = APIRouter()


class UptimeAlert(BaseModel):
    monitorID: Optional[int] = None
    monitorURL: Optional[str] = None
    monitorName: Optional[str] = None
    monitorStatus: Optional[int] = None
    alertType: Optional[str] = None
    alertMessage: Optional[str] = None
    alertDateTime: Optional[str] = None
    monitorType: Optional[str] = None
    monitorHostname: Optional[str] = None
    monitorPort: Optional[int] = None
    heartbeat: Optional[Any] = None
    monitor: Optional[Any] = None
    msg: Optional[str] = None


@router.post("/webhook/uptime-kuma")
async def uptime_kuma_webhook(alert: UptimeAlert, request: Request):
    try:
        print("🔍 === WEBHOOK UPTIME KUMA ===")

        if alert.msg and "Testing" in alert.msg:
            print(f"🧪 Тест: {alert.msg}")
            return {
                "success": True,
                "message": "Тестовое сообщение получено",
                "test_message": alert.msg,
                "timestamp": datetime.now().isoformat(),
            }

        monitor_name = None
        monitor_status = None
        monitor_type = None
        monitor_url = None
        monitor_hostname = None
        monitor_port = None
        alert_message = None

        if alert.heartbeat:
            monitor_status = alert.heartbeat.get("status")
            alert_message = alert.heartbeat.get("msg")

        if alert.monitor:
            monitor = alert.monitor
            monitor_name = monitor.get("name")
            monitor_type = monitor.get("type")
            monitor_url = monitor.get("url")
            monitor_hostname = monitor.get("hostname")
            monitor_port = monitor.get("port")

        if not monitor_name:
            monitor_name = alert.monitorName or alert.msg or "Unknown Monitor"
        if not alert_message:
            alert_message = (
                f"Status changed to {monitor_status}"
                if monitor_status is not None
                else "Status changed"
            )

        status_map = {0: "down", 1: "up", 2: "maintenance"}
        status = (
            status_map.get(monitor_status, "unknown")
            if monitor_status is not None
            else "unknown"
        )

        print(f"🚨 {monitor_name} — {status}: {alert_message}")

        details = {
            "monitor_name": monitor_name,
            "monitor_url": monitor_url or "N/A",
            "status": status,
            "alert_type": "status_change",
            "message": alert_message,
            "datetime": datetime.now().isoformat(),
            "monitor_type": monitor_type or "unknown",
            "hostname": monitor_hostname,
            "port": monitor_port,
        }

        incident_analysis = ""
        incident_analysis_full = ""
        analysis_type = "none"
        report_path = None

        if status in ("down", "error"):
            print("🔍 Анализ через Cursor CLI...")
            (
                incident_analysis_full,
                incident_analysis,
                report_path,
                analysis_type,
            ) = await generate_cursor_incident_analysis(
                monitor_name, status, details
            )
            print(
                f"✅ Анализ ({analysis_type}), telegram: {len(incident_analysis)} симв., "
                f"отчёт: {report_path}"
            )
        elif status == "up":
            incident_analysis = (
                f"🎉 **СЕРВИС ВОССТАНОВЛЕН: {monitor_name}**\n\n"
                f"✅ Сервис снова доступен.\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            analysis_type = "recovery"
        else:
            incident_analysis = (
                f"ℹ️ **СТАТУС: {monitor_name}** → {status}\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            analysis_type = "status_change"

        if RAG_AVAILABLE:
            try:
                incident_log = f"""
ИНЦИДЕНТ UPTIME KUMA:
Монитор: {monitor_name}
Статус: {status}
Анализ ({analysis_type}): {(incident_analysis_full or incident_analysis)[:800]}...
Отчёт: {report_path or 'N/A'}
"""
                add_log_to_rag(
                    incident_log,
                    {
                        "source": "uptime_kuma_webhook",
                        "kind": "incident_analysis",
                        "monitor_name": monitor_name,
                        "status": status,
                        "analysis_type": analysis_type,
                        "report_path": report_path or "",
                        "timestamp": details["datetime"],
                    },
                )
            except Exception as rag_error:
                print(f"⚠️ RAG: {rag_error}")

        vps_response = await send_to_vps(
            monitor_name,
            status,
            details,
            incident_analysis,
            analysis_type=analysis_type,
            report_path=report_path,
        )

        if vps_response.get("success"):
            print("✅ Отправлено на VPS → Telegram")
        else:
            print(f"❌ VPS: {vps_response.get('error')}")

        return {
            "success": True,
            "message": "Уведомление обработано",
            "incident_analysis": incident_analysis,
            "incident_analysis_chars": len(incident_analysis),
            "analysis_type": analysis_type,
            "report_path": report_path,
            "vps_response": vps_response,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_to_vps(
    service_name: str,
    status: str,
    details: Dict[str, Any],
    incident_analysis: str,
    analysis_type: str = "basic",
    report_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Отправка на VPS (далее Telegram) с анализом от Cursor CLI."""
    alert_data = {
        "source": "homelab_uptime_kuma",
        "timestamp": datetime.now().isoformat(),
        "service": service_name,
        "status": status,
        "details": details,
        "host": os.environ.get("HOMELAB_HOST", "localhost"),
        "webhook_type": "uptime_kuma",
        "incident_analysis": incident_analysis,
        "incident_severity": "high" if status in ("down", "error") else "normal",
        "analysis_type": analysis_type,
        "cursor_report_path": report_path,
    }

    vps_url = os.environ.get(
        "VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts"
    )

    print(f"📤 VPS: {vps_url}")

    try:
        response = requests.post(
            vps_url,
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if response.status_code == 200:
            return {"success": True, "message": "Отправлено на VPS", "response": response.text}
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text[:300]}",
        }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Таймаут VPS"}
    except requests.exceptions.ConnectionError as e:
        return {"success": False, "error": f"Подключение к VPS: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/webhook/uptime-kuma/health")
async def webhook_health():
    return {"status": "healthy", "service": "uptime-kuma-webhook"}


@router.post("/webhook/uptime-kuma/test-cursor")
async def test_cursor_analysis():
    """Тест Cursor CLI анализа."""
    test_details = {
        "monitor_name": "test-service",
        "monitor_url": "http://localhost:8080",
        "monitor_type": "http",
        "hostname": "localhost",
        "port": 8080,
        "message": "Connection timeout",
        "datetime": datetime.now().isoformat(),
    }
    full, telegram, report_path, analysis_type = await generate_cursor_incident_analysis(
        "test-service", "down", test_details
    )
    return {
        "success": analysis_type == "cursor_cli",
        "analysis_type": analysis_type,
        "report_path": report_path,
        "incident_analysis": telegram,
        "incident_analysis_chars": len(telegram),
        "timestamp": datetime.now().isoformat(),
    }
