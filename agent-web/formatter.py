"""
Форматирование ответов Homelab Agent в красивом стиле
"""

import re
from typing import Dict, Any, List

def format_agent_response(response: str) -> Dict[str, Any]:
    """
    Форматирует ответ агента в красивом JSON формате
    с поддержкой современного UI дизайна
    """
    
    # Очищаем и форматируем текст
    formatted_text = _clean_and_format_text(response)
    
    # Разбиваем на блоки для лучшего отображения
    blocks = _split_into_blocks(formatted_text)
    
    # Создаем структурированный ответ
    formatted_response = {
        "type": "agent_response",
        "content": {
            "text": formatted_text,
            "blocks": blocks,
            "metadata": _extract_metadata(response)
        },
        "styling": {
            "theme": "modern",
            "bubble_style": "gradient",
            "colors": {
                "primary": "#6366f1",
                "secondary": "#8b5cf6", 
                "accent": "#ec4899",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444"
            }
        }
    }
    
    return formatted_response

def _clean_and_format_text(text: str) -> str:
    """Очищает и форматирует текст ответа"""
    
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Форматируем заголовки
    text = re.sub(r'^# (.+)$', r'🎯 **\1**', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'📋 **\1**', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'💡 **\1**', text, flags=re.MULTILINE)
    
    # Форматируем списки
    text = re.sub(r'^- (.+)$', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'• \1', text, flags=re.MULTILINE)
    
    # Форматируем код
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'💻 **Код**:\n\2', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'🔧 `\1`', text)
    
    # Форматируем команды
    text = re.sub(r'```bash\n(.*?)\n```', r'🖥️ **Команда**:\n`\1`', text, flags=re.DOTALL)
    
    # Добавляем эмодзи для ключевых слов
    text = re.sub(r'\b(погода|weather)\b', r'🌤️ \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(статус|status)\b', r'📊 \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(сервис|service)\b', r'🔧 \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(ошибка|error)\b', r'❌ \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(успех|success)\b', r'✅ \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(новости|news)\b', r'📰 \1', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(технологии|technology)\b', r'🚀 \1', text, flags=re.IGNORECASE)
    
    return text.strip()

def _split_into_blocks(text: str) -> List[Dict[str, Any]]:
    """Разбивает текст на логические блоки для лучшего отображения"""
    
    blocks = []
    lines = text.split('\n')
    current_block = {"type": "text", "content": []}
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if current_block["content"]:
                blocks.append(current_block)
                current_block = {"type": "text", "content": []}
            continue
            
        # Определяем тип блока
        if line.startswith('🎯') or line.startswith('📋') or line.startswith('💡'):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "header", "content": [line]}
        elif line.startswith('•'):
            if current_block["type"] != "list":
                if current_block["content"]:
                    blocks.append(current_block)
                current_block = {"type": "list", "content": [line]}
            else:
                current_block["content"].append(line)
        elif line.startswith('💻') or line.startswith('🖥️'):
            if current_block["content"]:
                blocks.append(current_block)
            current_block = {"type": "code", "content": [line]}
        elif line.startswith('🔧 `') and line.endswith('`'):
            if current_block["type"] != "inline_code":
                if current_block["content"]:
                    blocks.append(current_block)
                current_block = {"type": "inline_code", "content": [line]}
            else:
                current_block["content"].append(line)
        else:
            if current_block["type"] != "text":
                if current_block["content"]:
                    blocks.append(current_block)
                current_block = {"type": "text", "content": [line]}
            else:
                current_block["content"].append(line)
    
    # Добавляем последний блок
    if current_block["content"]:
        blocks.append(current_block)
    
    return blocks

def _extract_metadata(text: str) -> Dict[str, Any]:
    """Извлекает метаданные из ответа"""
    
    metadata = {
        "has_code": "```" in text or "`" in text,
        "has_commands": "bash" in text.lower() or "команда" in text.lower(),
        "has_lists": any(line.strip().startswith('•') for line in text.split('\n')),
        "word_count": len(text.split()),
        "line_count": len(text.split('\n')),
        "topics": []
    }
    
    # Определяем темы
    topics = []
    if any(word in text.lower() for word in ['погода', 'weather', 'температура']):
        topics.append("weather")
    if any(word in text.lower() for word in ['сервис', 'статус', 'мониторинг']):
        topics.append("system_status")
    if any(word in text.lower() for word in ['новости', 'технологии', 'ai']):
        topics.append("news")
    if any(word in text.lower() for word in ['код', 'программа', 'скрипт']):
        topics.append("code")
    
    metadata["topics"] = topics
    
    return metadata

def create_simple_response(response: str, session_id: str) -> Dict[str, Any]:
    """
    Создает простой ответ в старом формате для обратной совместимости
    """
    return {
        "response": response,
        "session_id": session_id
    }

def create_enhanced_response(response: str, session_id: str) -> Dict[str, Any]:
    """
    Создает улучшенный ответ с форматированием
    """
    formatted = format_agent_response(response)
    
    return {
        "response": response,  # Оригинальный текст для совместимости
        "formatted": formatted,  # Новый форматированный ответ
        "session_id": session_id,
        "ui_enhanced": True
    }
