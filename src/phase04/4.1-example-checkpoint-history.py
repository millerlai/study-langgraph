# 4.1 範例：觀察 Checkpoint 的建立過程
# 展示遍歷所有 checkpoint，觀察每個 super-step 產生的 checkpoint 內容。

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
    print(f"  [node_a] 收到 state: foo={state['foo']}, bar={state['bar']}")
    return {"foo": "a", "bar": ["a"]}

def node_b(state: State) -> dict:
    print(f"  [node_b] 收到 state: foo={state['foo']}, bar={state['bar']}")
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

# === 5. 遍歷所有 checkpoint ===
print("\n=== 所有 Checkpoint（從新到舊） ===\n")
for i, state in enumerate(graph.get_state_history(config)):
    print(f"--- Checkpoint #{len(list(graph.get_state_history(config))) - 1 - i} ---")
    print(f"  values:  {state.values}")
    print(f"  next:    {state.next}")
    print(f"  source:  {state.metadata['source']}")
    print(f"  step:    {state.metadata['step']}")
    print(f"  writes:  {state.metadata['writes']}")
    print()
