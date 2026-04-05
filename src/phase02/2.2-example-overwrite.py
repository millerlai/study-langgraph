# 2.2 Reducer 機制 — Overwrite：繞過 Reducer 直接覆蓋
# 展示如何使用 Overwrite 在有 Reducer 的情況下強制覆蓋
# 不需要 API key

"""
Overwrite：繞過 Reducer 直接覆蓋
"""
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite

# ============================================================
# 1. 定義 State（messages 使用 add Reducer）
# ============================================================
class State(TypedDict):
    messages: Annotated[list[str], operator.add]

# ============================================================
# 2. 定義 Nodes
# ============================================================
def add_message(state: State) -> dict:
    """正常追加訊息（透過 Reducer）"""
    return {"messages": ["第一則訊息"]}

def add_more(state: State) -> dict:
    """繼續追加訊息（透過 Reducer）"""
    return {"messages": ["第二則訊息"]}

def reset_messages(state: State) -> dict:
    """重置訊息——用 Overwrite 繞過 Reducer"""
    return {"messages": Overwrite(["系統重置：清空所有歷史訊息"])}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(State)
builder.add_node("add_message", add_message)
builder.add_node("add_more", add_more)
builder.add_node("reset", reset_messages)
builder.add_edge(START, "add_message")
builder.add_edge("add_message", "add_more")
builder.add_edge("add_more", "reset")
builder.add_edge("reset", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({"messages": ["初始訊息"]})
print(result["messages"])
# ["系統重置：清空所有歷史訊息"]
#
# 過程：
# 初始:       ["初始訊息"]
# add_message: ["初始訊息", "第一則訊息"]          ← Reducer 追加
# add_more:    ["初始訊息", "第一則訊息", "第二則訊息"]  ← Reducer 追加
# reset:       ["系統重置：清空所有歷史訊息"]       ← Overwrite 直接取代！
