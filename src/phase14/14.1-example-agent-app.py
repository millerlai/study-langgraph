# 14.1 範例：完整的 LangGraph Agent 應用程式
# 可直接用 langgraph dev 或 langgraph up 啟動
# 需要：pip install langgraph langchain-core

from typing import Annotated, Literal
from typing_extensions import TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


# === 1. 定義 State ===
class AgentState(TypedDict):
    """Agent 的共享狀態"""
    messages: Annotated[list[AnyMessage], add_messages]
    step_count: int


# === 2. 定義 Node 函數 ===
def greet(state: AgentState) -> dict:
    """歡迎節點：產生歡迎訊息"""
    return {
        "messages": [{"role": "assistant", "content": "你好！我是你的 AI 助手。"}],
        "step_count": state.get("step_count", 0) + 1,
    }


def process(state: AgentState) -> dict:
    """處理節點：回覆使用者訊息"""
    last_msg = state["messages"][-1]
    content = getattr(last_msg, "content", str(last_msg))
    return {
        "messages": [
            {"role": "assistant", "content": f"收到您的訊息：{content}，正在處理中..."}
        ],
        "step_count": state.get("step_count", 0) + 1,
    }


def route(state: AgentState) -> Literal["process", "__end__"]:
    """路由邏輯：決定下一步"""
    if state.get("step_count", 0) >= 3:
        return "__end__"
    return "process"


# === 3. 建構 Graph ===
builder = StateGraph(AgentState)

builder.add_node("greet", greet)
builder.add_node("process", process)

builder.add_edge(START, "greet")
builder.add_conditional_edges("greet", route)
builder.add_edge("process", END)

# === 4. 編譯（供 Agent Server 使用，不需指定 checkpointer）===
graph = builder.compile()
