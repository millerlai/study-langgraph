# 15.1 範例：LangGraph + LangChain 自動追蹤
# 只需設定環境變數，無需額外程式碼
# 需要：pip install langgraph langchain-openai langchain-core
# 需要：設定 LANGSMITH_API_KEY 和 OPENAI_API_KEY 環境變數

import os
from typing import Literal, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages

# 確保 tracing 已啟用
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_xxxxx"  # 替換為你的 key


# === 定義工具 ===
@tool
def search(query: str) -> str:
    """搜尋網路上的資訊"""
    if "天氣" in query or "weather" in query.lower():
        return "今天台北 28 度，多雲時晴。"
    return "找到了一些相關資訊。"


# === 建構 Agent ===
tools = [search]
tool_node = ToolNode(tools)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    """決定是否呼叫工具"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"


def call_model(state: MessagesState) -> dict:
    """呼叫 LLM — LangSmith 會自動追蹤此呼叫"""
    response = model.invoke(state["messages"])
    return {"messages": [response]}


# === 建構 Graph ===
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# === 執行（自動產生 trace） ===
result = app.invoke(
    {"messages": [{"role": "user", "content": "台北今天天氣如何？"}]},
    config={"configurable": {"thread_id": "42"}},
)
print(result["messages"][-1].content)

# Trace 會自動出現在 LangSmith Dashboard 中
# 包含：每個 node 的執行時間、LLM 輸入/輸出、工具呼叫結果
