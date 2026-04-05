# 6.1 範例：updates 模式 - 僅變更的 key
# 展示 stream_mode="updates" 只串流每個節點實際變更的部分
"""
updates 模式：僅變更的 key
適合只關心每個節點做了什麼改變的場景
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class State(TypedDict):
    items: Annotated[list[str], operator.add]
    count: int
    metadata: str

def step_a(state: State) -> dict:
    # 只更新 items 和 count，不動 metadata
    return {"items": ["A 的輸出"], "count": 1}

def step_b(state: State) -> dict:
    # 只更新 metadata
    return {"metadata": "step_b 完成"}

def step_c(state: State) -> dict:
    # 更新所有欄位
    return {"items": ["C 的輸出"], "count": state["count"] + 1, "metadata": "全部完成"}

builder = StateGraph(State)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_node("step_c", step_c)
builder.add_edge(START, "step_a")
builder.add_edge("step_a", "step_b")
builder.add_edge("step_b", "step_c")
builder.add_edge("step_c", END)
graph = builder.compile()

# ============================================================
# stream_mode="updates"：僅變更的部分
# ============================================================
print("=== updates 模式 ===")
for chunk in graph.stream(
    {"items": [], "count": 0, "metadata": ""},
    stream_mode="updates",
    version="v2",
):
    print(f"[{chunk['type']}] {chunk['data']}")

# [updates] {'step_a': {'items': ['A 的輸出'], 'count': 1}}
# [updates] {'step_b': {'metadata': 'step_b 完成'}}
# [updates] {'step_c': {'items': ['C 的輸出'], 'count': 2, 'metadata': '全部完成'}}
