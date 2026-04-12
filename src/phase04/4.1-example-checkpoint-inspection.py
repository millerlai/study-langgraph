# 4.1 範例：檢視 Checkpoint 結構
# 展示如何取得最新 checkpoint 並檢視 StateSnapshot 的各個欄位。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State ===
class State(TypedDict):
    foo: str
    bar: Annotated[list[str], add]

# === 2. 定義節點 ===
def node_a(state: State) -> dict:
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State) -> dict:
    return {"foo": "b", "bar": ["b"]}

# === 3. 建構並編譯圖 ===
builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 4. 執行圖 ===
config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"foo": "", "bar": []}, config)

# === 5. 取得最新的 checkpoint ===
snapshot = graph.get_state(config)

print("=== 最新 Checkpoint ===")
print(f"values:        {snapshot.values}")
print(f"next:          {snapshot.next}")
print(f"checkpoint_id: {snapshot.config['configurable']['checkpoint_id']}")
print(f"source:        {snapshot.metadata['source']}")
print(f"step:          {snapshot.metadata['step']}")
print(f"writes:        {snapshot.metadata.get('writes', 'N/A')}")
print(f"created_at:    {snapshot.created_at}")
print(f"parent_config: {snapshot.parent_config}")
print(f"tasks:         {snapshot.tasks}")
