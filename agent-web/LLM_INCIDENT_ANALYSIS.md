# ⚠️ Устарело

Анализ инцидентов через **GigaChat + RAG** заменён на **Cursor CLI**.

| Было | Стало |
|------|--------|
| `generate_llm_incident_analysis()` | `agent/cursor_incident.py` |
| GigaChat в webhook | `agent -p --trust` в Docker |
| Длинный текст в Telegram | Сжатый шаблон ≤1400 символов |

Актуально: [INCIDENT_FLOW.md](INCIDENT_FLOW.md), [uptime_kuma_webhook_setup.md](uptime_kuma_webhook_setup.md).
