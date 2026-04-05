# 15.2 範例：供 Studio 連接的範例 agent
# 搭配 langgraph.json 使用，用 langgraph dev 啟動後可在 Studio 中操作
# 需要：pip install langgraph langchain-openai langchain-core
# 需要：設定 OPENAI_API_KEY 環境變數

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages


@tool
def search(query: str) -> str:
    """搜尋相關資訊"""
    return f"搜尋結果：關於 '{query}' 的資訊。"


@tool
def calculator(expression: str) -> str:
    """計算數學表達式"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"錯誤: {e}"


tools = [search, calculator]
tool_node = ToolNode(tools)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    if state["messages"][-1].tool_calls:
        return "tools"
    return "__end__"


def call_model(state: MessagesState) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response]}


# 建構 graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# 編譯（不需 checkpointer，Agent Server 會自動處理）
graph = workflow.compile()
