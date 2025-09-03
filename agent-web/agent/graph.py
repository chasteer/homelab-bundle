"""
Граф агента для Homelab на основе LangGraph
Использует правильную архитектуру с инструментами как узлами графа
"""

from typing import Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

from .tools import ALL_CUSTOM_TOOLS
from .llm import get_gigachat
from langchain_tavily import TavilySearchResults

# Инициализация LLM
llm = get_gigachat()

# Создаем список всех инструментов
search_tool = TavilySearchResults(max_results=3)

# Объединяем все инструменты
tools = [search_tool] + ALL_CUSTOM_TOOLS

# Привязываем инструменты к LLM
llm_with_tools = llm.bind_tools(tools)

# Создаем состояние
class State:
    messages: Annotated[list, add_messages]

# Создаем граф
graph_builder = StateGraph(State)

def chatbot(state: State):
    """Основной узел чат-бота"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Добавляем узлы
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Добавляем условные переходы
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")

# Устанавливаем точку входа
graph_builder.set_entry_point("chatbot")

# Компилируем граф с памятью
graph = graph_builder.compile(checkpointer=InMemorySaver())

def get_graph():
    """Получение скомпилированного графа"""
    return graph