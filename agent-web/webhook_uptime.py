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

# Импорт для LLM анализа
try:
    from agent.llm import get_gigachat
    from agent.rag import add_log_to_rag
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ LLM модуль недоступен, будет использован базовый анализ")

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

def generate_basic_incident_analysis(monitor_name: str, status: str, details: Dict[str, Any]) -> str:
    """Генерация детального анализа инцидента без LLM"""
    try:
        analysis = []
        analysis.append(f"🔍 **ДЕТАЛЬНЫЙ АНАЛИЗ ИНЦИДЕНТА: {monitor_name}**")
        analysis.append(f"📊 **Статус:** {status}")
        analysis.append(f"🌐 **URL:** {details.get('monitor_url', 'N/A')}")
        analysis.append(f"🖥️ **Тип монитора:** {details.get('monitor_type', 'N/A')}")
        analysis.append(f"🏠 **Хост:** {details.get('hostname', 'N/A')}")
        analysis.append(f"🔌 **Порт:** {details.get('port', 'N/A')}")
        analysis.append(f"⏰ **Время инцидента:** {details.get('datetime', 'N/A')}")
        
        # Добавляем дополнительную информацию если доступна
        if details.get('response_time'):
            analysis.append(f"⚡ **Время отклика:** {details.get('response_time')}ms")
        if details.get('uptime'):
            analysis.append(f"📈 **Uptime:** {details.get('uptime')}")
        if details.get('down_count'):
            analysis.append(f"🔴 **Количество падений:** {details.get('down_count')}")
        
        analysis.append("\n🚨 **ВОЗМОЖНЫЕ ПРИЧИНЫ:**")
        
        # Детальные рекомендации в зависимости от типа монитора
        monitor_type = details.get('monitor_type', '').lower()
        if 'http' in monitor_type or 'https' in monitor_type:
            analysis.append("   • Веб-сервер недоступен или не отвечает")
            analysis.append("   • Проблемы с конфигурацией nginx/apache")
            analysis.append("   • Сервис упал или завис")
            analysis.append("   • Проблемы с SSL сертификатами")
            analysis.append("   • Недостаточно ресурсов (CPU/RAM)")
        elif 'tcp' in monitor_type:
            analysis.append("   • Порт заблокирован файрволом")
            analysis.append("   • Сервис не запущен или упал")
            analysis.append("   • Проблемы с сетевыми настройками")
            analysis.append("   • Конфликт портов")
        elif 'ping' in monitor_type:
            analysis.append("   • Хост недоступен по сети")
            analysis.append("   • Проблемы с сетевым оборудованием")
            analysis.append("   • Хост выключен или перезагружается")
            analysis.append("   • Блокировка ICMP пакетов")
        elif 'dns' in monitor_type:
            analysis.append("   • DNS сервер недоступен")
            analysis.append("   • Проблемы с резолвингом домена")
            analysis.append("   • Неправильная конфигурация DNS")
        elif 'docker' in monitor_type or 'container' in monitor_type:
            analysis.append("   • Docker контейнер упал")
            analysis.append("   • Проблемы с Docker daemon")
            analysis.append("   • Недостаточно ресурсов для контейнера")
            analysis.append("   • Проблемы с volumes или networks")
        else:
            analysis.append("   • Сервис недоступен")
            analysis.append("   • Проблемы с подключением")
            analysis.append("   • Ошибки в конфигурации")
        
        analysis.append("\n🔧 **ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:**")
        
        # Специфичные действия для разных типов
        if 'http' in monitor_type or 'https' in monitor_type:
            analysis.append("   1. Проверить статус веб-сервера: `systemctl status nginx` или `systemctl status apache2`")
            analysis.append("   2. Проверить логи: `tail -f /var/log/nginx/error.log`")
            analysis.append("   3. Проверить доступность порта: `netstat -tlnp | grep :80` или `netstat -tlnp | grep :443`")
            analysis.append("   4. Проверить SSL сертификаты: `openssl s_client -connect localhost:443`")
        elif 'tcp' in monitor_type:
            analysis.append("   1. Проверить статус сервиса: `systemctl status <service_name>`")
            analysis.append("   2. Проверить логи: `journalctl -u <service_name> -f`")
            analysis.append("   3. Проверить файрвол: `ufw status` или `iptables -L`")
            analysis.append("   4. Проверить занятость порта: `lsof -i :<port>`")
        elif 'docker' in monitor_type or 'container' in monitor_type:
            analysis.append("   1. Проверить статус контейнера: `docker ps -a`")
            analysis.append("   2. Посмотреть логи: `docker logs <container_name>`")
            analysis.append("   3. Проверить ресурсы: `docker stats <container_name>`")
            analysis.append("   4. Перезапустить контейнер: `docker restart <container_name>`")
        else:
            analysis.append("   1. Проверить статус сервиса: `systemctl status <service_name>`")
            analysis.append("   2. Проверить логи: `journalctl -u <service_name> -f`")
            analysis.append("   3. Проверить доступность порта: `netstat -tlnp | grep <port>`")
            analysis.append("   4. Перезапустить сервис: `systemctl restart <service_name>`")
        
        analysis.append("\n📋 **ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:**")
        analysis.append("   • Мониторинг ресурсов: `htop`, `iotop`, `df -h`")
        analysis.append("   • Сетевые подключения: `ss -tuln`, `netstat -i`")
        analysis.append("   • Проверка конфигурации: `nginx -t`, `apache2ctl configtest`")
        analysis.append("   • Проверка прав доступа: `ls -la /path/to/service`")
        analysis.append("   • Проверка зависимостей: `systemctl list-dependencies <service>`")
        
        analysis.append("\n🚀 **АВТОМАТИЧЕСКИЕ ДЕЙСТВИЯ:**")
        analysis.append("   • Попытка автоматического перезапуска: `systemctl restart <service>`")
        analysis.append("   • Проверка через 30 секунд после перезапуска")
        analysis.append("   • Уведомление администратора при повторных падениях")
        
        analysis.append("\n⚠️ **ПРИМЕЧАНИЕ:** Это детальный анализ на основе правил. Для более точной диагностики используйте LLM агента.")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"❌ Ошибка генерации детального анализа: {str(e)}"

async def generate_llm_incident_analysis(monitor_name: str, status: str, details: Dict[str, Any]) -> str:
    """Генерация детального анализа инцидента с использованием LLM"""
    try:
        if not LLM_AVAILABLE:
            print("⚠️ LLM недоступен, используем базовый анализ")
            return generate_basic_incident_analysis(monitor_name, status, details)
        
        # Получаем LLM
        llm = get_gigachat()
        if llm is None:
            print("⚠️ LLM не инициализирован, используем базовый анализ")
            return generate_basic_incident_analysis(monitor_name, status, details)
        
        # Формируем промпт для LLM
        prompt = f"""
Ты - эксперт по DevOps и системному администрированию. Проанализируй следующий инцидент и предоставь детальный анализ.

ИНЦИДЕНТ:
- Монитор: {monitor_name}
- Статус: {status}
- Тип монитора: {details.get('monitor_type', 'unknown')}
- URL: {details.get('monitor_url', 'N/A')}
- Сообщение: {details.get('message', 'No message')}
- Время: {details.get('datetime', 'N/A')}
- Хост: {details.get('hostname', 'N/A')}
- Порт: {details.get('port', 'N/A')}

ПРОВЕДИ ДЕТАЛЬНЫЙ АНАЛИЗ:

1. **АНАЛИЗ ПРИЧИН** - возможные причины инцидента
2. **ДИАГНОСТИКА** - команды для диагностики проблемы
3. **РЕШЕНИЕ** - пошаговые действия по устранению
4. **ПРОФИЛАКТИКА** - меры для предотвращения повторения
5. **ОЦЕНКА СЕРЬЕЗНОСТИ** - критичность инцидента (low/medium/high/critical)

Используй технический опыт и предоставь конкретные команды и рекомендации.
Формат ответа: используй markdown с заголовками, списками и блоками кода.
"""
        
        print(f"🤖 Генерируем LLM анализ для {monitor_name}...")
        
        # Вызываем LLM
        try:
            response = llm.invoke(prompt)
            llm_analysis = response.content if hasattr(response, 'content') else str(response)
            
            # Записываем инцидент в RAG
            incident_log = f"""
ИНЦИДЕНТ UPTIME KUMA (LLM АНАЛИЗ):
Монитор: {monitor_name}
Статус: {status}
Тип: {details.get('monitor_type', 'unknown')}
URL: {details.get('monitor_url', 'N/A')}
Сообщение: {details.get('message', 'No message')}
Время: {details.get('datetime', 'N/A')}
LLM Анализ: {llm_analysis[:500]}...
"""
            
            log_metadata = {
                "source": "uptime_kuma_webhook",
                "kind": "incident_analysis_llm",
                "monitor_name": monitor_name,
                "status": status,
                "monitor_type": details.get('monitor_type', 'unknown'),
                "timestamp": details.get('datetime', datetime.now().isoformat()),
                "analysis_type": "llm"
            }
            
            add_log_to_rag(incident_log, log_metadata)
            
            print(f"✅ LLM анализ сгенерирован и сохранен в RAG")
            return llm_analysis
            
        except Exception as llm_error:
            print(f"❌ Ошибка LLM анализа: {llm_error}, используем базовый анализ")
            return generate_basic_incident_analysis(monitor_name, status, details)
        
    except Exception as e:
        print(f"❌ Ошибка генерации LLM анализа: {str(e)}")
        return generate_basic_incident_analysis(monitor_name, status, details)

@router.post("/webhook/uptime-kuma")
async def uptime_kuma_webhook(alert: UptimeAlert, request: Request):
    """Обработка вебхука от Uptime Kuma"""
    try:
        # Детальное логирование входящего запроса
        print(f"🔍 === ВХОДЯЩИЙ WEBHOOK ОТ UPTIME KUMA ===")
        
        # Логируем заголовки
        print(f"📝 Заголовки:")
        for header, value in request.headers.items():
            print(f"   - {header}: {value}")
        
        print(f"📝 Тип данных: {type(alert)}")
        print(f"📝 Данные: {alert}")
        print(f"📝 JSON представление: {alert.model_dump_json(indent=2)}")
        print(f"📝 Атрибуты:")
        print(f"   - msg: {alert.msg}")
        print(f"   - monitorID: {alert.monitorID}")
        print(f"   - monitorName: {alert.monitorName}")
        print(f"   - monitorStatus: {alert.monitorStatus}")
        print(f"   - alertMessage: {alert.alertMessage}")
        print(f"   - alertType: {alert.alertType}")
        print(f"   - monitorType: {alert.monitorType}")
        print(f"   - monitorHostname: {alert.monitorHostname}")
        print(f"   - monitorPort: {alert.monitorPort}")
        print(f"   - heartbeat: {alert.heartbeat}")
        print(f"   - monitor: {alert.monitor}")
        print(f"🔍 === КОНЕЦ ЛОГИРОВАНИЯ ===")
        
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
        
        # Это реальное уведомление - извлекаем данные из heartbeat и monitor
        monitor_name = None
        monitor_status = None
        monitor_type = None
        monitor_url = None
        monitor_hostname = None
        monitor_port = None
        alert_message = None
        
        # Извлекаем данные из heartbeat
        if alert.heartbeat:
            heartbeat = alert.heartbeat
            monitor_status = heartbeat.get('status')  # 0 = down, 1 = up
            alert_message = heartbeat.get('msg')
            print(f"📊 Данные из heartbeat: status={monitor_status}, msg={alert_message}")
        
        # Извлекаем данные из monitor
        if alert.monitor:
            monitor = alert.monitor
            monitor_name = monitor.get('name')
            monitor_type = monitor.get('type')
            monitor_url = monitor.get('url')
            monitor_hostname = monitor.get('hostname')
            monitor_port = monitor.get('port')
            print(f"📊 Данные из monitor: name={monitor_name}, type={monitor_type}, url={monitor_url}")
        
        # Если имя монитора не найдено, используем сообщение
        if not monitor_name:
            monitor_name = alert.msg or "Unknown Monitor"
        
        # Если сообщение не найдено, создаем дефолтное
        if not alert_message:
            alert_message = f"Status changed to {monitor_status}" if monitor_status is not None else "Status changed"
        
        print(f"🔍 Извлеченные данные: name={monitor_name}, status={monitor_status}, type={monitor_type}")
        
        # Логируем уведомление
        print(f"🚨 Получено уведомление от Uptime Kuma: {monitor_name} - {alert_message}")
        
        # Определяем статус
        status_map = {0: "down", 1: "up", 2: "maintenance"}
        status = status_map.get(monitor_status, "unknown") if monitor_status is not None else "unknown"
        
        # Формируем детали для агента
        details = {
            "monitor_name": monitor_name,
            "monitor_url": monitor_url or "N/A",
            "status": status,
            "alert_type": "status_change",
            "message": alert_message,
            "datetime": datetime.now().isoformat(),
            "monitor_type": monitor_type or "unknown",
            "hostname": monitor_hostname,
            "port": monitor_port
        }
        
        # Генерируем детальный анализ инцидента (для всех статусов)
        incident_analysis = ""
        if status in ["down", "error"]:
            print(f"🔍 Генерируем детальный анализ инцидента...")
            # Используем LLM анализ если доступен
            incident_analysis = await generate_llm_incident_analysis(monitor_name, status, details)
            print(f"✅ Детальный анализ сгенерирован")
        elif status == "up":
            print(f"✅ Сервис восстановлен: {monitor_name}")
            incident_analysis = f"🎉 **СЕРВИС ВОССТАНОВЛЕН: {monitor_name}**\n\n✅ Сервис снова доступен и работает корректно.\n⏰ Время восстановления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            print(f"ℹ️ Статус: {status} для {monitor_name}")
            incident_analysis = f"ℹ️ **ИЗМЕНЕНИЕ СТАТУСА: {monitor_name}**\n\n📊 Новый статус: {status}\n⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Записываем все инциденты в RAG для истории
        try:
            if LLM_AVAILABLE:
                incident_log = f"""
ИНЦИДЕНТ UPTIME KUMA:
Монитор: {monitor_name}
Статус: {status}
Тип: {monitor_type or 'unknown'}
URL: {monitor_url or 'N/A'}
Сообщение: {alert_message}
Время: {datetime.now().isoformat()}
Анализ: {incident_analysis[:500]}...
"""
                
                log_metadata = {
                    "source": "uptime_kuma_webhook",
                    "kind": "incident_analysis",
                    "monitor_name": monitor_name,
                    "status": status,
                    "monitor_type": monitor_type or 'unknown',
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": "llm" if status in ["down", "error"] else "basic"
                }
                
                add_log_to_rag(incident_log, log_metadata)
                print(f"✅ Инцидент записан в RAG")
        except Exception as rag_error:
            print(f"⚠️ Ошибка записи в RAG: {rag_error}")
        
        # Отправляем уведомление на VPS с анализом
        vps_response = await send_to_vps(monitor_name, status, details, incident_analysis)
        
        # Логируем результат отправки на VPS
        if vps_response.get("success"):
            print(f"✅ Уведомление успешно отправлено на VPS")
        else:
            print(f"❌ Ошибка отправки на VPS: {vps_response.get('error', 'Неизвестная ошибка')}")
        
        # Возвращаем результат
        return {
            "success": True,
            "message": "Уведомление обработано",
            "incident_analysis": incident_analysis,
            "vps_response": vps_response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка обработки вебхука: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {str(e)}")

async def send_to_vps(service_name: str, status: str, details: Dict[str, Any], incident_analysis: str) -> Dict[str, Any]:
    """Отправка уведомления на VPS с анализом инцидента"""
    try:
        # Данные для отправки
        alert_data = {
            "source": "homelab_uptime_kuma",
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "status": status,
            "details": details,
            "host": os.environ.get("HOMELAB_HOST", "localhost"),
            "webhook_type": "uptime_kuma",
            "incident_analysis": incident_analysis,  # Добавляем анализ инцидента
            "incident_severity": "high" if status in ["down", "error"] else "normal",
            "analysis_type": "llm" if status in ["down", "error"] else "basic"  # Указываем тип анализа
        }
        
        # Отправляем на VPS
        vps_url = os.environ.get("VPS_WEBHOOK_URL", "https://your_vps_domain.com/api/uptime-alerts")
        
        print(f"📤 Отправка уведомления на VPS: {vps_url}")
        print(f"📋 Данные: {json.dumps(alert_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            vps_url,
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📥 Ответ от VPS: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Успешно отправлено на VPS")
            return {"success": True, "message": "Отправлено на VPS", "response": response.text}
        elif response.status_code == 404:
            print(f"❌ Эндпоинт на VPS не найден (404). Проверьте URL: {vps_url}")
            return {"success": False, "error": f"Эндпоинт не найден (404). Проверьте URL: {vps_url}"}
        else:
            print(f"❌ Ошибка отправки на VPS: HTTP {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout:
        error_msg = "Таймаут при отправке на VPS"
        print(f"⏰ {error_msg}")
        return {"success": False, "error": error_msg}
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Ошибка подключения к VPS: {str(e)}"
        print(f"🔌 {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Неожиданная ошибка при отправке на VPS: {str(e)}"
        print(f"💥 {error_msg}")
        return {"success": False, "error": error_msg}

@router.get("/webhook/uptime-kuma/health")
async def webhook_health():
    """Проверка здоровья вебхука"""
    return {
        "status": "healthy",
        "service": "uptime-kuma-webhook"
    }

@router.post("/webhook/uptime-kuma/test-llm")
async def test_llm_analysis():
    """Тестирование LLM анализа инцидентов"""
    try:
        # Тестовые данные инцидента
        test_details = {
            "monitor_name": "test-service",
            "monitor_url": "http://localhost:8080",
            "monitor_type": "http",
            "hostname": "localhost",
            "port": 8080,
            "message": "Connection timeout",
            "message": "Connection timeout",
            "datetime": datetime.now().isoformat()
        }
        
        print("🧪 Тестируем LLM анализ...")
        
        # Генерируем LLM анализ
        incident_analysis = await generate_llm_incident_analysis("test-service", "down", test_details)
        
        return {
            "success": True,
            "message": "LLM анализ протестирован",
            "incident_analysis": incident_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Ошибка тестирования LLM: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }