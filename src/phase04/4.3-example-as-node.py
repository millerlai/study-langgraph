# 4.3 範例：as_node 參數
# 展示 update_state 的 as_node 參數如何控制下一步執行哪個節點。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

# === 1. 定義 State 和節點 ===
class State(TypedDict):
    value: str

def node_a(state: State) -> dict:
    return {"value": state["value"] + " -> A"}

def node_b(state: State) -> dict:
    return {"value": state["value"] + " -> B"}

def node_c(state: State) -> dict:
    return {"value": state["value"] + " -> C"}

# === 2. 建構圖: A -> B -> C ===
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
config = {"configurable": {"thread_id": "as_node_demo"}}
result = graph.invoke({"value": "Start"}, config)
print(f"完整結果: {result['value']}")
# 完整結果: Start -> A -> B -> C

# === 4. 找到 node_a 執行前的 checkpoint ===
history = list(graph.get_state_history(config))
before_a = next(s for s in history if s.next == ("node_a",))

# === 5. 使用 as_node="node_a"：假裝是 node_a 產生的，下一步執行 node_b ===
fork_config = graph.update_state(
    before_a.config,
    values={"value": "Modified"},
    as_node="node_a",  # 假裝 node_a 已經執行
)

fork_result = graph.invoke(None, fork_config)
print(f"跳過 node_a: {fork_result['value']}")
# 跳過 node_a: Modified -> B -> C
# node_a 被跳過，從 node_b 開始執行

# === 6. 使用 as_node="node_b"：假裝 node_b 也完成了 ===
fork_config2 = graph.update_state(
    before_a.config,
    values={"value": "Skip to C"},
    as_node="node_b",  # 假裝 node_a 和 node_b 都已執行
)

fork_result2 = graph.invoke(None, fork_config2)
print(f"跳到 node_c: {fork_result2['value']}")
# 跳到 node_c: Skip to C -> C
