# 4.1 範例：沒有 Checkpointer vs. 有 Checkpointer
# 展示使用 checkpointer 後，同一 thread 的多次 invoke 會接續上次的 State。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

class State(TypedDict):
    count: int

def increment(state: State) -> dict:
    return {"count": state["count"] + 1}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_edge(START, "increment")
builder.add_edge("increment", END)

# === 沒有 checkpointer：每次從頭開始 ===
graph_no_cp = builder.compile()
r1 = graph_no_cp.invoke({"count": 0})
print(r1)  # {'count': 1}
r2 = graph_no_cp.invoke({"count": 0})
print(r2)  # {'count': 1}  ← 每次都從 0 開始

# === 有 checkpointer：接續上次的 State ===
graph_with_cp = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "counter_thread"}}

r1 = graph_with_cp.invoke({"count": 0}, config)
print(r1)  # {'count': 1}
r2 = graph_with_cp.invoke({"count": 0}, config)
print(r2)  # {'count': 2}  ← 接續上次的 count=1
r3 = graph_with_cp.invoke({"count": 0}, config)
print(r3)  # {'count': 3}  ← 接續上次的 count=2
