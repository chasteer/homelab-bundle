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
from .llm import get_llm
from langchain_community.tools.tavily_search import TavilySearchResults


# Инициализация LLM
llm = get_llm()

# Создаем список всех инструментов
search_tool = TavilySearchResults(max_results=5)  # Увеличиваем количество результатов

# Объединяем все инструменты
tools = [search_tool] + ALL_CUSTOM_TOOLS

# Системный промпт для агента
SYSTEM_PROMPT = """Ты - Homelab Agent, умный помощник для управления домашней лабораторией.

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

ПОМНИ: Ты можешь искать информацию в реальном времени - используй эту возможность!"""

# Привязываем инструменты к LLM (только если LLM доступен)
if llm is not None:
    llm_with_tools = llm.bind_tools(tools)
else:
    llm_with_tools = None

# Создаем состояние
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Создаем граф
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Основной узел чат-бота"""
    # Добавляем системный промпт к каждому запросу
    messages = state["messages"]
    
    # Проверяем, доступен ли LLM
    if llm_with_tools is None:
        # Если LLM недоступен, возвращаем сообщение об ошибке
        error_message = AIMessage(content="❌ **Ошибка LLM**\n\nGigaChat API недоступен. Возможные причины:\n- Неверный токен авторизации\n- Проблемы с сетью\n- Изменения в API GigaChat\n\nПожалуйста, проверьте настройки GigaChat в переменных окружения.")
        return {"messages": [error_message]}
    
    # Если это первый запрос, добавляем системный промпт
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        system_message = HumanMessage(content=f"{SYSTEM_PROMPT}\n\nЗапрос пользователя: {messages[0].content}")
        messages = [system_message]
    
    try:
        return {"messages": [llm_with_tools.invoke(messages)]}
    except Exception as e:
        # Если произошла ошибка при вызове LLM, возвращаем сообщение об ошибке
        error_message = AIMessage(content=f"❌ **Ошибка LLM**\n\nПроизошла ошибка при обращении к GigaChat API:\n\n```\n{str(e)}\n```\n\nПожалуйста, проверьте настройки и попробуйте снова.")
        return {"messages": [error_message]}

# Создаем узел для инструментов
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