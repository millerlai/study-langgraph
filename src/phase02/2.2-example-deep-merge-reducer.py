# 2.2 Reducer 機制 — 自定義 Reducer：深度合併字典
# 展示如何用自定義 Reducer 實現字典的深度合併
# 不需要 API key

"""
自定義 Reducer：深度合併字典
"""
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

def deep_merge(current: dict, new: dict) -> dict:
    """深度合併兩個字典"""
    merged = {**current}
    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged

class State(TypedDict):
    config: Annotated[dict, deep_merge]

def set_defaults(state: State) -> dict:
    return {"config": {"model": "gpt-4o", "temperature": 0.7, "options": {"stream": True}}}

def override_model(state: State) -> dict:
    return {"config": {"model": "claude-sonnet", "options": {"timeout": 30}}}

builder = StateGraph(State)
builder.add_node("defaults", set_defaults)
builder.add_node("override", override_model)
builder.add_edge(START, "defaults")
builder.add_edge("defaults", "override")
builder.add_edge("override", END)

graph = builder.compile()

result = graph.invoke({"config": {}})
print(result["config"])
# {
#     "model": "claude-sonnet",        ← 被覆蓋
#     "temperature": 0.7,              ← 保留
#     "options": {
#         "stream": True,              ← 保留（深度合併）
#         "timeout": 30                ← 新增（深度合併）
#     }
# }
