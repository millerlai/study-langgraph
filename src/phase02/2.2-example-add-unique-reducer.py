# 2.2 Reducer 機制 — 自定義 Reducer：移除重複項的列表串接
# 展示去重串接的自定義 Reducer
# 不需要 API key

"""
自定義 Reducer：移除重複項的列表串接
"""
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

def add_unique(current: list[str], new: list[str]) -> list[str]:
    """串接列表但自動去除重複項"""
    seen = set(current)
    result = list(current)
    for item in new:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result

class State(TypedDict):
    tags: Annotated[list[str], add_unique]

def node_a(state: State) -> dict:
    return {"tags": ["python", "ai", "langgraph"]}

def node_b(state: State) -> dict:
    return {"tags": ["ai", "agent", "langgraph"]}  # "ai" 和 "langgraph" 已存在

builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)

graph = builder.compile()

result = graph.invoke({"tags": []})
print(result["tags"])
# ["python", "ai", "langgraph", "agent"]
# 注意："ai" 和 "langgraph" 沒有重複出現
