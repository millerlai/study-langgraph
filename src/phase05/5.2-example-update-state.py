# 5.2 範例：使用 update_state() 直接修改 State
# 展示在中斷期間用 update_state() 修改 Agent 的 State 後恢復執行
"""
使用 update_state() 在中斷期間直接修改 State
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

class State(TypedDict):
    draft: str
    reviewed: bool
    final: str

def generate_draft(state: State) -> dict:
    """生成草稿"""
    return {"draft": "LangGraph 是一個用於建構 AI agent 的框架。它很好用。"}

def finalize(state: State) -> dict:
    """最終化"""
    return {"final": f"[已審核] {state['draft']}"}

builder = StateGraph(State)
builder.add_node("generate_draft", generate_draft)
builder.add_node("finalize", finalize)
builder.add_edge(START, "generate_draft")
builder.add_edge("generate_draft", "finalize")
builder.add_edge("finalize", END)

checkpointer = MemorySaver()

# 在 generate_draft 之後暫停
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_after=["generate_draft"],
)

config = {"configurable": {"thread_id": "edit-state-1"}}

# 第一次呼叫：執行 generate_draft 後暫停
graph.invoke({"draft": "", "reviewed": False, "final": ""}, config=config)

# 檢查草稿
state = graph.get_state(config)
print(f"原始草稿: {state.values['draft']}")
# 原始草稿: LangGraph 是一個用於建構 AI agent 的框架。它很好用。

# ============================================================
# 用 update_state() 直接修改 State
# ============================================================
graph.update_state(
    config,
    values={
        "draft": "LangGraph 是一個強大的低階 AI agent 編排框架，"
                 "提供精細的狀態管理和流程控制。",
        "reviewed": True,
    },
)

# 確認修改
state = graph.get_state(config)
print(f"修改後草稿: {state.values['draft']}")
print(f"已審核: {state.values['reviewed']}")
# 修改後草稿: LangGraph 是一個強大的低階 AI agent 編排框架，提供精細的狀態管理和流程控制。
# 已審核: True

# 恢復執行
result = graph.invoke(Command(resume=None), config=config)
print(f"最終結果: {result['final']}")
# 最終結果: [已審核] LangGraph 是一個強大的低階 AI agent 編排框架，提供精細的狀態管理和流程控制。
