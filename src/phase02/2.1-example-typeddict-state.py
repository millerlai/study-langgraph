# 2.1 State Schema 設計 — 使用 TypedDict 定義 State 的完整範例
# 展示 TypedDict 作為 State Schema 的基本用法
# 不需要 API key

"""
使用 TypedDict 定義 State 的完整範例
"""
from typing import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State Schema
# ============================================================
class AgentState(TypedDict):
    messages: list[AnyMessage]   # 對話訊息列表
    task: str                    # 目前任務描述
    iteration: int               # 迭代次數
    result: str                  # 最終結果

# ============================================================
# 2. 定義 Nodes
# ============================================================
def initialize(state: AgentState) -> dict:
    """初始化節點：設定初始值"""
    return {
        "task": state.get("task", "未指定"),
        "iteration": 0,
        "result": "",
    }

def process(state: AgentState) -> dict:
    """處理節點：模擬處理邏輯"""
    current_iteration = state["iteration"]
    task = state["task"]
    return {
        "iteration": current_iteration + 1,
        "result": f"已完成任務「{task}」的第 {current_iteration + 1} 次處理",
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(AgentState)
builder.add_node("initialize", initialize)
builder.add_node("process", process)
builder.add_edge(START, "initialize")
builder.add_edge("initialize", "process")
builder.add_edge("process", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({
    "messages": [],
    "task": "分析報告",
    "iteration": 0,
    "result": "",
})

print(result)
# {
#     "messages": [],
#     "task": "分析報告",
#     "iteration": 1,
#     "result": "已完成任務「分析報告」的第 1 次處理"
# }
