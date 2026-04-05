# 4.3 範例：get_state 取得目前 State
# 展示取得指定 thread 的最新 checkpoint，並檢視 StateSnapshot 欄位。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State 和節點 ===
class State(TypedDict):
    messages: Annotated[list[str], add]
    step_count: int

def step_a(state: State) -> dict:
    return {"messages": ["step_a 完成"], "step_count": 1}

def step_b(state: State) -> dict:
    return {"messages": ["step_b 完成"], "step_count": 2}

# === 2. 建構圖 ===
builder = StateGraph(State)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_edge(START, "step_a")
builder.add_edge("step_a", "step_b")
builder.add_edge("step_b", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 3. 執行圖 ===
config = {"configurable": {"thread_id": "get_state_demo"}}
result = graph.invoke({"messages": ["開始"], "step_count": 0}, config)

# === 4. 取得最新 State ===
snapshot = graph.get_state(config)

print("=== 最新 State ===")
print(f"values:     {snapshot.values}")
print(f"next:       {snapshot.next}")
print(f"step:       {snapshot.metadata['step']}")
print(f"source:     {snapshot.metadata['source']}")
print(f"writes:     {snapshot.metadata['writes']}")
print(f"created_at: {snapshot.created_at}")
