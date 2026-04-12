# 4.3 範例：get_state_history 查詢 State 歷史
# 展示取得指定 thread 的所有 checkpoint 歷史，按時間由新到舊排列。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State 和節點 ===
class State(TypedDict):
    value: str
    history: Annotated[list[str], add]

def node_a(state: State) -> dict:
    return {"value": "a", "history": ["visited_a"]}

def node_b(state: State) -> dict:
    return {"value": "b", "history": ["visited_b"]}

def node_c(state: State) -> dict:
    return {"value": "c", "history": ["visited_c"]}

# === 2. 建構圖 ===
builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("node_c", node_c)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", "node_c")
builder.add_edge("node_c", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 3. 執行圖 ===
config = {"configurable": {"thread_id": "history_demo"}}
result = graph.invoke({"value": "start", "history": ["init"]}, config)

# === 4. 取得完整歷史 ===
all_states = list(graph.get_state_history(config))

print(f"共 {len(all_states)} 個 checkpoint（由新到舊）\n")

for i, state in enumerate(all_states):
    print(f"--- [{i}] step={state.metadata['step']}, "
          f"source={state.metadata['source']} ---")
    print(f"  values:  {state.values}")
    print(f"  next:    {state.next}")
    print(f"  writes:  {state.metadata.get('writes', 'N/A')}")
    print()
