"""
Анализ инцидентов через Cursor CLI (headless: `agent -p --trust`).
Устанавливается в Docker: curl https://cursor.com/install | bash
"""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

INCIDENTS_DIR = Path(os.environ.get("CURSOR_INCIDENTS_DIR", "/app/logs/incidents"))

# Кандидаты: standalone CLI (предпочтительно), затем desktop wrapper
_CLI_CANDIDATES = [
    os.environ.get("CURSOR_CLI_PATH", ""),
    "/home/agent/.local/bin/agent",
    shutil.which("agent") or "",
    "/usr/local/bin/agent",
    "cursor",  # cursor agent ...
]


def resolve_cursor_cli() -> str:
    """Возвращает путь к рабочему бинарнику agent/cursor."""
    seen: set[str] = set()
    for raw in _CLI_CANDIDATES:
        if not raw or raw in seen:
            continue
        seen.add(raw)
        path = Path(raw)
        if path.name == "cursor" and path.is_file():
            return str(path)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        found = shutil.which(raw)
        if found:
            return found
    raise RuntimeError(
        "Cursor CLI не найден. В Docker: пересоберите образ (curl cursor.com/install). "
        "На хосте: curl https://cursor.com/install -fsS | bash"
    )


def check_cursor_cli_available() -> Dict[str, Any]:
    """Проверка для /api/health."""
    try:
        cli = resolve_cursor_cli()
        result = subprocess.run(
            _version_cmd(cli),
            capture_output=True,
            text=True,
            timeout=15,
            env=_cli_env(),
        )
        ok = result.returncode == 0
        version = (result.stdout or result.stderr or "").strip().split("\n")[0]
        return {
            "cursor_cli_available": ok,
            "cursor_cli_path": cli,
            "cursor_cli_version": version if ok else None,
            "cursor_api_key_set": bool(os.environ.get("CURSOR_API_KEY")),
            "cursor_workspace": os.environ.get("CURSOR_WORKSPACE", "/app/homelab"),
            "error": None if ok else (result.stderr or result.stdout or "")[:300],
        }
    except Exception as e:
        return {
            "cursor_cli_available": False,
            "cursor_cli_path": None,
            "cursor_api_key_set": bool(os.environ.get("CURSOR_API_KEY")),
            "error": str(e),
        }


def _version_cmd(cli: str) -> List[str]:
    if Path(cli).name == "cursor":
        return [cli, "agent", "--version"]
    return [cli, "--version"]


def _cli_env() -> Dict[str, str]:
    env = os.environ.copy()
    home = env.get("HOME", "/home/agent")
    env["HOME"] = home
    env["PATH"] = f"{home}/.local/bin:" + env.get("PATH", "")
    env["NO_COLOR"] = "1"
    env["TERM"] = "dumb"
    Path(home, ".cursor").mkdir(parents=True, exist_ok=True)
    key = os.environ.get("CURSOR_API_KEY")
    if key:
        env["CURSOR_API_KEY"] = key
    return env


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text).strip()


def _parse_agent_output(stdout: str, stderr: str) -> str:
    """Извлекает текст ответа из text или json (stream-json) вывода agent."""
    chunks: List[str] = []
    for raw in (stdout or "", stderr or ""):
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    chunks.append(_strip_ansi(line))
                    continue
                if obj.get("type") == "result":
                    if obj.get("is_error"):
                        raise RuntimeError(
                            str(obj.get("result") or obj.get("error") or "Agent error")
                        )
                    if obj.get("result"):
                        return _strip_ansi(str(obj["result"]))
                if obj.get("type") == "assistant":
                    for block in obj.get("message", {}).get("content", []):
                        if block.get("type") == "text" and block.get("text"):
                            chunks.append(block["text"])
            else:
                chunks.append(_strip_ansi(line))

    text = "\n".join(c for c in chunks if c).strip()
    if text:
        return text

    combined = _strip_ansi((stdout or "") + "\n" + (stderr or "")).strip()
    return combined


def _build_agent_cmd(cli: str, workspace: str, prompt: str) -> List[str]:
    """Собирает argv для standalone agent или `cursor agent`."""
    model = os.environ.get("CURSOR_AGENT_MODEL", "").strip()
    mode = os.environ.get("CURSOR_AGENT_MODE", "plan").strip()
    output_format = os.environ.get("CURSOR_OUTPUT_FORMAT", "json").strip()

    base = [cli] if Path(cli).name != "cursor" else [cli, "agent"]
    cmd = base + [
        "-p",
        "--trust",
        "--approve-mcps",
        "--sandbox",
        "disabled",
        "--output-format",
        output_format,
        "--workspace",
        workspace,
    ]

    if mode in ("plan", "ask"):
        cmd.extend(["--mode", mode])
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_")[:80] or "unknown"


def _telegram_max_chars() -> int:
    try:
        return max(400, int(os.environ.get("CURSOR_TELEGRAM_MAX_CHARS", "1400")))
    except ValueError:
        return 1400


def build_incident_prompt(monitor_name: str, status: str, details: Dict[str, Any]) -> str:
    max_chars = _telegram_max_chars()
    return f"""Homelab alert. Write ONLY the final report for Telegram — Russian, markdown.

DATA:
- monitor: {monitor_name}
- status: {status}
- type: {details.get('monitor_type', 'unknown')}
- url: {details.get('monitor_url', 'N/A')}
- message: {details.get('message', 'N/A')}

Repo: Docker Compose in services/, agent-web/, container names like jellyfin, uptime-kuma, immich-server.

RULES (mandatory):
- Max {max_chars} characters total. Stop when limit reached.
- NO preamble ("ищу", "анализирую", "сейчас проверю", "forming plan").
- NO copying large configs or logs.
- NO section "Профилактика" unless critical.
- Use EXACTLY this structure (4 blocks only):

**Причина:** 1–2 short sentences.

**Проверить:**
`command 1`
`command 2`
(max 3 commands, one line each)

**Исправить:**
1. step one
2. step two
(max 4 steps, one line each)

**Серьёзность:** low|medium|high|critical
"""


def format_analysis_for_telegram(analysis: str, report_path: Optional[str] = None) -> str:
    """Сжимает ответ Cursor для Telegram; полный текст остаётся в файле отчёта."""
    text = _strip_ansi(analysis).strip()
    if not text:
        return text

    # Убираем типичные «процессные» вступления
    skip_patterns = (
        r"^(ищу|сейчас|анализирую|проверяю|формирую|looking|searching)",
        r"^(данные инцидента|incident data)",
    )
    lines: List[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if any(re.match(p, low) for p in skip_patterns):
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines).strip()

    max_len = _telegram_max_chars()
    if len(text) <= max_len:
        return text

    cut = text[: max_len - 80].rstrip()
    # обрезка по последнему переводу строки
    if "\n" in cut:
        cut = cut.rsplit("\n", 1)[0]
    suffix = "…"
    if report_path:
        suffix += f"\n\n_Полный отчёт: `{report_path}`_"
    else:
        suffix += "\n\n_(сообщение обрезано)_"
    return cut + suffix


def _save_report(monitor_name: str, status: str, analysis: str) -> str:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = INCIDENTS_DIR / f"{ts}_{_slug(monitor_name)}_{status}.md"
    header = (
        f"# Incident: {monitor_name}\n\n"
        f"- **Status:** {status}\n"
        f"- **Time:** {datetime.now().isoformat()}\n\n---\n\n"
    )
    path.write_text(header + analysis, encoding="utf-8")
    return str(path)


def analyze_via_cursor_cli(
    monitor_name: str,
    status: str,
    details: Dict[str, Any],
) -> Tuple[str, str]:
    cli = resolve_cursor_cli()
    workspace = os.environ.get(
        "CURSOR_WORKSPACE",
        os.environ.get("HOMELAB_REPO_PATH", "/app/homelab"),
    )
    if not os.path.isdir(workspace):
        raise RuntimeError(f"CURSOR_WORKSPACE не существует: {workspace}")

    if not os.environ.get("CURSOR_API_KEY"):
        raise RuntimeError(
            "CURSOR_API_KEY не задан — нужен ключ из https://cursor.com/dashboard"
        )

    timeout = int(os.environ.get("CURSOR_CLI_TIMEOUT", "300"))
    prompt = build_incident_prompt(monitor_name, status, details)
    cmd = _build_agent_cmd(cli, workspace, prompt)

    print(f"🤖 Cursor CLI: {cli} (workspace={workspace}, mode={os.environ.get('CURSOR_AGENT_MODE', 'plan')})")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_cli_env(),
            cwd=workspace,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise RuntimeError(f"Cursor CLI не найден: {cli}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Cursor CLI timeout ({timeout}s)")

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if result.returncode != 0:
        err = _strip_ansi(stderr or stdout).strip()
        raise RuntimeError(f"Cursor CLI exit {result.returncode}: {err[:800]}")

    try:
        analysis = _parse_agent_output(stdout, stderr)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Ошибка разбора ответа Cursor CLI: {e}") from e

    if not analysis:
        preview = _strip_ansi(stderr or stdout)[:500]
        raise RuntimeError(
            "Cursor CLI вернул пустой ответ. "
            f"Проверьте CURSOR_API_KEY и сеть из контейнера. Вывод: {preview!r}"
        )

    report_path = _save_report(monitor_name, status, analysis)
    print(f"✅ Отчёт: {report_path}")
    return analysis, report_path


def generate_basic_incident_analysis(
    monitor_name: str, status: str, details: Dict[str, Any]
) -> str:
    return (
        f"**Причина:** сервис {monitor_name} недоступен ({status}). Cursor CLI не ответил.\n\n"
        f"**Проверить:**\n"
        f"`docker ps -a | grep -i {monitor_name.split()[0].lower()}`\n"
        f"`docker logs {monitor_name} --tail 50`\n\n"
        f"**Исправить:**\n"
        f"1. `docker restart {monitor_name}`\n"
        f"2. Проверить `services/docker-compose.yml`\n\n"
        f"**Серьёзность:** medium"
    )


async def generate_cursor_incident_analysis(
    monitor_name: str,
    status: str,
    details: Dict[str, Any],
) -> Tuple[str, str, Optional[str], str]:
    """
    Returns: (full_analysis, telegram_analysis, report_path, analysis_type)
    """
    if os.environ.get("CURSOR_INCIDENT_ENABLED", "true").lower() != "true":
        basic = generate_basic_incident_analysis(monitor_name, status, details)
        path = _save_report(monitor_name, status, basic)
        return basic, format_analysis_for_telegram(basic, path), path, "disabled"

    require_cli = os.environ.get("CURSOR_INCIDENT_REQUIRED", "true").lower() == "true"

    try:
        full, report_path = analyze_via_cursor_cli(monitor_name, status, details)
        telegram = format_analysis_for_telegram(full, report_path)
        return full, telegram, report_path, "cursor_cli"
    except Exception as e:
        print(f"⚠️ Cursor CLI: {e}")
        if require_cli:
            err_text = f"❌ **Ошибка Cursor CLI**\n\n`{str(e)[:400]}`"
            path = _save_report(monitor_name, status, err_text)
            return err_text, err_text, path, "cursor_cli_error"
        basic = generate_basic_incident_analysis(monitor_name, status, details)
        path = _save_report(monitor_name, status, basic)
        return basic, format_analysis_for_telegram(basic, path), path, "basic"
