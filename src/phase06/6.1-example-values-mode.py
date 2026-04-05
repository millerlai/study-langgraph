# 6.1 範例：values 模式 - 每步完整 State
# 展示 stream_mode="values" 在每個節點執行完後串流完整的 State 快照
"""
values 模式：每步完整 State
適合需要看到圖的完整狀態演進的場景
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import operator

class State(TypedDict):
    items: Annotated[list[str], operator.add]
    count: int

def step_a(state: State) -> dict:
    return {"items": ["A 的輸出"], "count": 1}

def step_b(state: State) -> dict:
    return {"items": ["B 的輸出"], "count": state["count"] + 1}

def step_c(state: State) -> dict:
    return {"items": ["C 的輸出"], "count": state["count"] + 1}

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
# stream_mode="values"：每步完整 State
# ============================================================
print("=== values 模式 ===")
for chunk in graph.stream(
    {"items": ["初始"], "count": 0},
    stream_mode="values",
    version="v2",
):
    print(f"[{chunk['type']}] items={chunk['data']['items']}, count={chunk['data']['count']}")

# [values] items=['初始'], count=0                           <- 初始 State
# [values] items=['初始', 'A 的輸出'], count=1               <- step_a 後
# [values] items=['初始', 'A 的輸出', 'B 的輸出'], count=2   <- step_b 後
# [values] items=['初始', 'A 的輸出', 'B 的輸出', 'C 的輸出'], count=3  <- step_c 後
