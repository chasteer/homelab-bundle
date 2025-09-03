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
from .llm import get_gigachat
from langchain_community.tools.tavily_search import TavilySearchResults


# Инициализация LLM
llm = get_gigachat()

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

ПРИМЕРЫ:
- Вопрос о погоде → используй TavilySearch для получения актуальных данных
- Технический вопрос → используй соответствующий инструмент
- Неизвестная информация → ищи через доступные инструменты

ПОМНИ: Ты можешь искать информацию в реальном времени - используй эту возможность!"""

# GigaChat не поддерживает инструменты в текущей версии
# Используем базовый LLM с системным промптом
llm_with_tools = llm

# Создаем состояние
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Создаем граф
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Основной узел чат-бота"""
    # Добавляем системный промпт к каждому запросу
    messages = state["messages"]
    
    # Если это первый запрос, добавляем системный промпт
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        system_message = HumanMessage(content=f"{SYSTEM_PROMPT}\n\nЗапрос пользователя: {messages[0].content}")
        messages = [system_message]
    
    return {"messages": [llm_with_tools.invoke(messages)]}

# Добавляем узлы
graph_builder.add_node("chatbot", chatbot)

# Устанавливаем точку входа
graph_builder.set_entry_point("chatbot")

# Компилируем граф с памятью
graph = graph_builder.compile(checkpointer=InMemorySaver())

def get_graph():
    """Получение скомпилированного графа"""
    return graph