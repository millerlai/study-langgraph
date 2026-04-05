# 2.2 Reducer 機制 — 使用 Annotated 語法指定 Reducer
# 展示有 Reducer 和無 Reducer 的欄位行為差異
# 不需要 API key

"""
使用 Annotated 語法指定 Reducer
展示有 Reducer 和無 Reducer 的欄位行為差異
"""
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State（混合使用 Reducer 和預設行為）
# ============================================================
class State(TypedDict):
    # 無 Reducer → 覆蓋
    status: str

    # 有 Reducer → operator.add → 累加
    logs: Annotated[list[str], add]
    total: Annotated[int, add]

# ============================================================
# 2. 定義 Nodes
# ============================================================
def step_1(state: State) -> dict:
    return {
        "status": "step_1_done",
        "logs": ["[Step 1] 開始處理"],
        "total": 10,
    }

def step_2(state: State) -> dict:
    return {
        "status": "step_2_done",     # 會覆蓋 "step_1_done"
        "logs": ["[Step 2] 完成"],   # 會追加到 logs 列表
        "total": 20,                 # 會加到 total（10 + 20 = 30）
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("step_2", step_2)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({
    "status": "init",
    "logs": [],
    "total": 0,
})

print(result)
# {
#     "status": "step_2_done",                  ← 被覆蓋（無 Reducer）
#     "logs": ["[Step 1] 開始處理", "[Step 2] 完成"],  ← 累加（有 Reducer）
#     "total": 30,                              ← 相加 0+10+20=30（有 Reducer）
# }
