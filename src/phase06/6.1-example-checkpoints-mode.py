# 6.1 範例：checkpoints 模式 - 串流 checkpoint 資訊
# 展示 stream_mode="checkpoints" 追蹤 State 的持久化狀態
"""
checkpoints 模式：串流每個 checkpoint 的資訊
適合追蹤 State 的持久化狀態
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    value: int

def increment(state: State) -> dict:
    return {"value": state["value"] + 1}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_edge(START, "increment")
builder.add_edge("increment", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "cp-demo"}}

print("=== checkpoints 模式 ===")
for chunk in graph.stream(
    {"value": 0},
    config=config,
    stream_mode="checkpoints",
    version="v2",
):
    data = chunk["data"]
    if isinstance(data, dict):
        cp_config = data.get("config", {}).get("configurable", {})
        print(f"  checkpoint_id={cp_config.get('checkpoint_id', 'N/A')}, "
              f"checkpoint_ns={cp_config.get('checkpoint_ns', 'N/A')}")
