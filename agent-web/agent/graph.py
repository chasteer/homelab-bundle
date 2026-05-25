"""
Граф агента для Homelab на основе LangGraph
Использует правильную архитектуру с инструментами как узлами графа
"""

import os
from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

from .tools import ALL_CUSTOM_TOOLS
from .uptime_kuma_tools import UPTIME_KUMA_TOOLS
from .uptime_kuma_socketio_tools import UPTIME_KUMA_SOCKETIO_TOOLS
# from .memory_tools import MEMORY_TOOLS, set_session_id  # Временно отключено для Groq
from .llm import get_llm
from langchain_community.tools.tavily_search import TavilySearchResults


# Инициализация LLM
llm = get_llm()

# Создаем список всех инструментов
search_tool = TavilySearchResults(max_results=5)  # Увеличиваем количество результатов

# Объединяем все инструменты (память временно отключена для Groq)
tools = [search_tool] + ALL_CUSTOM_TOOLS + UPTIME_KUMA_TOOLS + UPTIME_KUMA_SOCKETIO_TOOLS  # + MEMORY_TOOLS

# Отладочная информация
print(f"🔧 Загружено инструментов: {len(tools)}")
# print(f"🧠 Инструменты памяти: {[tool.name for tool in MEMORY_TOOLS]}")  # Временно отключено

# Системный промпт для агента
SYSTEM_PROMPT = """Ты - Homelab Agent, умный помощник для управления домашней лабораторией.

🧠 **ПАМЯТЬ АГЕНТА:**
ℹ️ Если пользователь говорит "запомни" - используй save_to_memory() или remember_user_preference()
ℹ️ Если пользователь спрашивает "как меня зовут", "что я предпочитаю", "что ты помнишь" - используй get_from_memory() или get_user_preference()

ТВОИ ОСНОВНЫЕ ПРИНЦИПЫ:
1. ВСЕГДА используй доступные инструменты для получения актуальной информации
2. Если не знаешь ответ или не имеешь доступа к данным - ИСПОЛЬЗУЙ ПОИСК
3. Для вопросов о погоде, новостях, актуальной информации - используй TavilySearch
4. Для технических вопросов - используй специализированные инструменты
5. Отвечай точно и по делу, основываясь на найденной информации

🚨 **КРИТИЧЕСКИ ВАЖНО:**
- НИКОГДА не придумывай данные - ВСЕГДА используй инструменты!
- Если просят найти что-то - ВЫЗЫВАЙ search_incident_history
- Если просят статистику - ВЫЗЫВАЙ get_incident_statistics
- Если просят анализ - ВЫЗЫВАЙ analyze_incident_with_llm

🚨 **ВАЖНО - ИСПОЛЬЗУЙ ИНСТРУМЕНТЫ РЕАЛЬНО:**
- Когда просят найти информацию - ВЫЗЫВАЙ search_incident_history
- Когда просят статистику - ВЫЗЫВАЙ get_incident_statistics  
- Когда просят анализ - ВЫЗЫВАЙ analyze_incident_with_llm
- НЕ ПРОСТО ОПИСЫВАЙ, КАК ИХ ИСПОЛЬЗОВАТЬ - ВЫПОЛНЯЙ ИХ!

🎯 **ПРАВИЛО: Если пользователь просит найти, показать или проанализировать что-то - ВСЕГДА используй соответствующий инструмент!**

ВАЖНО - ОТВЕЧАЙ НА ВОПРОСЫ:
- Если спрашивают о статусе homelab - давай КОНКРЕТНУЮ информацию о текущем состоянии
- Если спрашивают о погоде - давай АКТУАЛЬНЫЕ данные о погоде
- Если спрашивают о новостях - давай ПОСЛЕДНИЕ новости
- НЕ давай инструкции "как это сделать" если не просят

ФОРМАТ ОТВЕТОВ:
- Используй четкие заголовки с # ## ###
- Структурируй информацию в списки с - или *
- Выделяй код в ```блоках
- Используй **жирный текст** для важной информации
- Добавляй эмодзи для лучшего восприятия

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
- TavilySearch: для поиска актуальной информации (погода, новости, события)
- Системные инструменты: информация о системе, Docker, GitHub
- Анализ кода: проверка качества и стиля кода
- Мониторинг: состояние сервисов homelab
- Uptime Kuma: мониторинг и отчеты о состоянии системы
- ПАМЯТЬ АГЕНТА: сохранение и извлечение информации в рамках сессии

НОВЫЕ ВОЗМОЖНОСТИ МОНИТОРИНГА:
- monitor_uptime_kuma(): получение актуального статуса мониторинга
- generate_uptime_report(): генерация полного отчета с рекомендациями
- send_uptime_alert(): отправка уведомлений о проблемах

🚨 **АНАЛИЗ ИНЦИДЕНТОВ С LLM:**
- analyze_incident_with_llm(): детальный анализ инцидентов с использованием LLM и RAG
- search_incident_history(): поиск по истории инцидентов в базе данных
- get_incident_statistics(): статистика по инцидентам и их анализу

🔍 **RAG И БАЗА ДАННЫХ:**
- Автоматическое сохранение всех инцидентов в базу данных
- Поиск похожих случаев для контекстного анализа
- Интеграция с LLM для умного анализа проблем

🧠 **ПАМЯТЬ АГЕНТА:**
- save_to_memory(): сохранение информации для использования в рамках сессии
- get_from_memory(): извлечение сохраненной информации по ключу
- list_memory_keys(): просмотр всех сохраненных ключей
- get_conversation_history(): получение истории разговора
- remember_user_preference(): запоминание предпочтений пользователя
- get_user_preference(): получение сохраненных предпочтений

🎯 **КРИТИЧЕСКИ ВАЖНО - ИСПОЛЬЗУЙ ПАМЯТЬ АВТОМАТИЧЕСКИ:**
- Когда пользователь говорит "запомни", "запиши", "сохрани" - СРАЗУ ВЫЗОВИ save_to_memory() или remember_user_preference()
- Когда пользователь спрашивает "что ты помнишь", "что я говорил", "как меня зовут" - СРАЗУ ВЫЗОВИ get_from_memory() или get_user_preference()
- Когда пользователь упоминает свое имя, предпочтения, настройки - АВТОМАТИЧЕСКИ СОХРАНИ через remember_user_preference()
- ПЕРЕД ответом на вопрос о пользователе - СНАЧАЛА ПРОВЕРЬ память через get_from_memory()
- НЕ ОТВЕЧАЙ "я не знаю" - СНАЧАЛА ПРОВЕРЬ ПАМЯТЬ!

ПРИМЕРЫ:
- Вопрос о погоде → используй TavilySearch для получения актуальных данных
- Технический вопрос → используй соответствующий инструмент
- Неизвестная информация → ищи через доступные инструменты
- Вопрос о мониторинге → используй monitor_uptime_kuma для получения актуального статуса
- Вопрос о состоянии системы → используй generate_uptime_report для полного анализа
- Анализ инцидента → используй analyze_incident_with_llm для детального LLM анализа
- Поиск по истории → используй search_incident_history для поиска похожих случаев
- Статистика инцидентов → используй get_incident_statistics для аналитики

🚨 **КОНКРЕТНЫЕ ПРИМЕРЫ ВЫЗОВА:**
- "Найди все случаи падения" → ВЫЗОВИ search_incident_history("падение сервисов")
- "Покажи статистику" → ВЫЗОВИ get_incident_statistics()
- "Проанализируй инцидент" → ВЫЗОВИ analyze_incident_with_llm(данные_инцидента)

🧠 **ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ПАМЯТИ:**
- "Запомни, что я предпочитаю Python" → ВЫЗОВИ remember_user_preference("language", "Python")
- "Меня зовут Иван" → ВЫЗОВИ remember_user_preference("name", "Иван")
- "Запомни, что проект называется MyApp" → ВЫЗОВИ save_to_memory("project_name", "MyApp", "project")
- "Что я предпочитаю?" → ВЫЗОВИ get_user_preference("language")
- "Что я говорил о проекте?" → ВЫЗОВИ get_from_memory("project_name", "project")

**ПАМЯТЬ:**
- ВОПРОС "Как меня зовут?" → используй get_user_preference("name")
- ВОПРОС "Что я предпочитаю?" → используй get_user_preference("language")
- ВОПРОС "Что ты помнишь?" → используй list_memory_keys()

ПОМНИ: Ты можешь искать информацию в реальном времени - используй эту возможность!"""

# Привязываем инструменты к LLM (только если LLM доступен)
if llm is not None:
    try:
        llm_with_tools = llm.bind_tools(tools)
        print(f"✅ LLM с инструментами инициализирован успешно")
        print(f"🔧 Количество инструментов: {len(tools)}")
    except Exception as e:
        print(f"❌ Ошибка привязки инструментов к LLM: {e}")
        llm_with_tools = None
else:
    llm_with_tools = None

# Создаем состояние
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str  # Добавляем session_id в состояние

# Создаем граф
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Основной узел чат-бота"""
    # Добавляем системный промпт к каждому запросу
    messages = state["messages"]
    session_id = state.get("session_id", "default")
    
    # Проверяем, доступен ли LLM
    if llm_with_tools is None:
        # Если LLM недоступен, возвращаем сообщение об ошибке
        error_message = AIMessage(content="❌ **Ошибка LLM**\n\nLLM API недоступен. Возможные причины:\n- Неверный токен авторизации\n- Проблемы с сетью\n- Изменения в API\n\nПожалуйста, проверьте настройки API в переменных окружения.")
        return {"messages": [error_message]}
    
    # Если это первый запрос, добавляем системный промпт с session_id
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        system_message = HumanMessage(content=f"{SYSTEM_PROMPT}\n\nТЕКУЩАЯ СЕССИЯ: {session_id}\n\nЗапрос пользователя: {messages[0].content}")
        messages = [system_message]
    
    try:
        response = llm_with_tools.invoke(messages)
        print(f"🔍 LLM ответ: {type(response)}")
        print(f"🔍 Содержимое: {response.content[:100]}...")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"🔧 Вызовы инструментов: {len(response.tool_calls)}")
            for i, call in enumerate(response.tool_calls):
                print(f"  {i+1}. {call.get('name', 'unknown')}: {call.get('args', {})}")
        else:
            print("ℹ️ Нет вызовов инструментов")
        return {"messages": [response]}
    except Exception as e:
        # Если произошла ошибка при вызове LLM, пробуем переключить модель
        print(f"❌ Ошибка в chatbot: {e}")
        
        # Проверяем, является ли это ошибкой модели (rate limit, over capacity, etc.)
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['rate limit', 'over capacity', 'not found', 'timeout', '429', '503', '404']):
            print("🔄 Обнаружена ошибка модели, пробуем переключить...")
            
            # Импортируем функцию переключения моделей
            from .llm import get_groq_with_fallback, GROQ_MODELS
            
            # Получаем текущую модель из LLM
            current_model = getattr(llm_with_tools, 'model_name', None) if llm_with_tools else None
            
            # Пробуем переключиться на другую модель
            new_llm, new_model = get_groq_with_fallback(current_model)
            
            if new_llm is not None:
                print(f"✅ Переключились на модель: {new_model}")
                try:
                    # Создаем новый LLM с инструментами
                    new_llm_with_tools = new_llm.bind_tools(tools)
                    print(f"✅ LLM с инструментами обновлен для модели: {new_model}")
                    
                    # Пробуем повторить запрос с новой моделью
                    response = new_llm_with_tools.invoke(messages)
                    print(f"🔍 LLM ответ (новая модель): {type(response)}")
                    return {"messages": [response]}
                except Exception as retry_error:
                    print(f"❌ Ошибка при повторном запросе: {retry_error}")
        
        # Если переключение не помогло, возвращаем сообщение об ошибке
        error_message = AIMessage(content=f"❌ **Ошибка LLM**\n\nПроизошла ошибка при обращении к LLM API:\n\n```\n{str(e)}\n```\n\nПопробовал переключить модель, но проблема сохраняется. Пожалуйста, проверьте настройки и попробуйте снова.")
        return {"messages": [error_message]}

# Создаем узел для инструментов с поддержкой session_id (временно отключено для Groq)
# def tool_node_with_session(state: State):
#     """Узел для инструментов с установкой session_id"""
#     session_id = state.get("session_id", "default")
#     set_session_id(session_id)
#     
#     # Создаем стандартный узел инструментов
#     tool_node = ToolNode(tools)
#     return tool_node.invoke(state)

# Используем стандартный ToolNode без поддержки памяти
tool_node = ToolNode(tools)

# Добавляем узлы
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# Добавляем условные ребра
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "tools",
        END: END
    }
)

# Добавляем ребро от инструментов обратно к чат-боту
graph_builder.add_edge("tools", "chatbot")

# Устанавливаем точку входа
graph_builder.set_entry_point("chatbot")

# Компилируем граф с памятью
graph = graph_builder.compile(checkpointer=InMemorySaver())

def get_graph():
    """Получение скомпилированного графа"""
    return graph