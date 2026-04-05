# 4.2 範例：Checkpoint Namespace（父圖/子圖）
# 展示父圖和子圖的 checkpoint namespace 機制。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from typing import TypedDict

# === 1. 定義 State ===
class State(TypedDict):
    value: str

# === 2. 定義節點——透過 config 取得 namespace ===
def my_node(state: State, config: RunnableConfig) -> dict:
    checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
    if checkpoint_ns == "":
        print("  我在父圖中執行")
    else:
        print(f"  我在子圖中執行，namespace: {checkpoint_ns}")
    return {"value": f"processed in ns={checkpoint_ns}"}

# === 3. 建立子圖 ===
sub_builder = StateGraph(State)
sub_builder.add_node("sub_node", my_node)
sub_builder.add_edge(START, "sub_node")
sub_builder.add_edge("sub_node", END)
subgraph = sub_builder.compile()

# === 4. 建立父圖（包含子圖作為節點） ===
parent_builder = StateGraph(State)
parent_builder.add_node("parent_node", my_node)
parent_builder.add_node("child_graph", subgraph)
parent_builder.add_edge(START, "parent_node")
parent_builder.add_edge("parent_node", "child_graph")
parent_builder.add_edge("child_graph", END)

checkpointer = InMemorySaver()
parent_graph = parent_builder.compile(checkpointer=checkpointer)

# === 5. 執行 ===
config = {"configurable": {"thread_id": "ns_demo"}}
result = parent_graph.invoke({"value": "hello"}, config)

# 輸出:
#   我在父圖中執行
#   我在子圖中執行，namespace: child_graph:xxxxxxxx-xxxx-...
