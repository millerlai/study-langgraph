# 6.1 範例：debug 模式 - 最詳細的除錯資訊
# 展示 stream_mode="debug" 輸出每個節點的輸入/輸出/時間戳等詳細資訊
"""
debug 模式：最詳細的資訊，包含每個節點的輸入/輸出/時間戳
適合開發和除錯
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int

def add_one(state: State) -> dict:
    return {"value": state["value"] + 1}

def double(state: State) -> dict:
    return {"value": state["value"] * 2}

builder = StateGraph(State)
builder.add_node("add_one", add_one)
builder.add_node("double", double)
builder.add_edge(START, "add_one")
builder.add_edge("add_one", "double")
builder.add_edge("double", END)
graph = builder.compile()

print("=== debug 模式 ===")
for chunk in graph.stream(
    {"value": 5},
    stream_mode="debug",
    version="v2",
):
    data = chunk["data"]
    # debug chunk 包含 type (如 "task", "task_result") 和詳細資訊
    if isinstance(data, dict):
        event_type = data.get("type", "unknown")
        print(f"  [{event_type}] payload keys: {list(data.get('payload', {}).keys()) if isinstance(data.get('payload'), dict) else 'N/A'}")

# debug 模式輸出非常詳細，包含：
# - task: 節點開始執行
# - task_result: 節點執行完成，包含輸入/輸出/時間
