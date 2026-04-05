# 2.2 Reducer 機制 — 預設 Reducer 行為：直接覆蓋
# 展示無 Reducer 時，State 欄位的覆蓋行為
# 不需要 API key

"""
預設 Reducer 行為：直接覆蓋
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State（無 Reducer——全部用預設覆蓋行為）
# ============================================================
class State(TypedDict):
    foo: int             # 預設 Reducer → 覆蓋
    bar: list[str]       # 預設 Reducer → 覆蓋（整個 list 被取代！）

# ============================================================
# 2. 定義 Nodes
# ============================================================
def node_a(state: State) -> dict:
    """只更新 foo"""
    return {"foo": 10}

def node_b(state: State) -> dict:
    """更新 bar"""
    return {"bar": ["from_node_b"]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({"foo": 1, "bar": ["initial"]})
print(result)
# {"foo": 10, "bar": ["from_node_b"]}
#
# 注意：bar 的 ["initial"] 被完全覆蓋為 ["from_node_b"]
# 而非追加為 ["initial", "from_node_b"]
