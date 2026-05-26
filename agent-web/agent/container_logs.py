"""
Сбор логов Docker-контейнера для анализа инцидентов (homelab-agent имеет docker.sock).
"""

import os
import re
import subprocess
from typing import Dict, Optional

# Имя монитора Uptime Kuma → имя контейнера Docker
MONITOR_TO_CONTAINER: Dict[str, str] = {
    "jellyfin": "jellyfin",
    "torrserver": "torrserver",
    "immich": "immich-server",
    "immich-server": "immich-server",
    "vaultwarden": "vaultwarden",
    "uptime-kuma": "uptime-kuma",
    "uptime kuma": "uptime-kuma",
    "homelab-agent": "homelab-agent",
    "agent": "homelab-agent",
    "caddy": "caddy",
    "it-tools": "it-tools",
    "homeassistant": "homeassistant",
    "home assistant": "homeassistant",
    "dozzle": "dozzle",
    "homelab": "homelab-agent",
}


def _default_tail() -> int:
    try:
        return max(30, min(500, int(os.environ.get("CONTAINER_LOG_TAIL", "150"))))
    except ValueError:
        return 150


def resolve_container_name(monitor_name: str) -> Optional[str]:
    if not monitor_name:
        return None
    key = monitor_name.strip().lower()
    if key in MONITOR_TO_CONTAINER:
        return MONITOR_TO_CONTAINER[key]
    slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    if slug in MONITOR_TO_CONTAINER:
        return MONITOR_TO_CONTAINER[slug]
    # homelab-agent-db, immich-postgres, …
    if slug.replace("-", "") in key.replace("-", ""):
        for name, container in MONITOR_TO_CONTAINER.items():
            if name in key or key in name:
                return container
    return slug if slug else None


def fetch_container_logs(
    container: str,
    tail: Optional[int] = None,
    timeout: Optional[int] = None,
) -> str:
    """Последние строки docker logs (или сообщение об ошибке)."""
    tail = tail or _default_tail()
    timeout = timeout or int(os.environ.get("CONTAINER_LOG_TIMEOUT", "30"))
    cmd = [
        "docker",
        "logs",
        container,
        "--tail",
        str(tail),
        "--timestamps",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return "docker CLI не найден в контейнере агента"
    except subprocess.TimeoutExpired:
        return f"таймаут docker logs ({timeout}s) для {container}"
    except Exception as e:
        return f"ошибка docker logs: {e}"

    out = (result.stdout or "") + (result.stderr or "")
    out = out.strip()
    if result.returncode != 0 and not out:
        return f"docker logs {container} exit {result.returncode} (контейнер остановлен?)"
    if not out:
        return f"(логи {container} пусты)"
    max_chars = int(os.environ.get("CONTAINER_LOG_MAX_CHARS", "12000"))
    if len(out) > max_chars:
        out = "…\n" + out[-max_chars:]
    return out


def attach_container_logs(details: dict) -> None:
    """Дополняет details полями container_name и container_logs."""
    monitor = details.get("monitor_name") or ""
    container = resolve_container_name(monitor)
    details["container_name"] = container
    if not container:
        details["container_logs"] = "(не удалось сопоставить имя контейнера)"
        return
    print(f"📋 Логи контейнера: {container} (tail {_default_tail()})")
    details["container_logs"] = fetch_container_logs(container)
