# 4.2 範例：子圖獨立 Checkpoint
# 展示使用 checkpointer=True 讓子圖有獨立的 checkpoint 歷史。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State ===
class State(TypedDict):
    steps: Annotated[list[str], add]

# === 2. 定義子圖節點 ===
def sub_step_a(state: State) -> dict:
    return {"steps": ["sub_a 完成"]}

def sub_step_b(state: State) -> dict:
    return {"steps": ["sub_b 完成"]}

# === 3. 建立有獨立 checkpointer 的子圖 ===
sub_builder = StateGraph(State)
sub_builder.add_node("sub_step_a", sub_step_a)
sub_builder.add_node("sub_step_b", sub_step_b)
sub_builder.add_edge(START, "sub_step_a")
sub_builder.add_edge("sub_step_a", "sub_step_b")
sub_builder.add_edge("sub_step_b", END)

# checkpointer=True 表示子圖使用獨立 checkpoint
subgraph = sub_builder.compile(checkpointer=True)

# === 4. 建立父圖 ===
def parent_step(state: State) -> dict:
    return {"steps": ["parent 完成"]}

parent_builder = StateGraph(State)
parent_builder.add_node("parent_step", parent_step)
parent_builder.add_node("my_subgraph", subgraph)
parent_builder.add_edge(START, "parent_step")
parent_builder.add_edge("parent_step", "my_subgraph")
parent_builder.add_edge("my_subgraph", END)

checkpointer = InMemorySaver()
parent_graph = parent_builder.compile(checkpointer=checkpointer)

# === 5. 執行並查看子圖 checkpoint ===
config = {"configurable": {"thread_id": "subgraph_cp_demo"}}
result = parent_graph.invoke({"steps": ["開始"]}, config)
print(result["steps"])
# ['開始', 'parent 完成', 'sub_a 完成', 'sub_b 完成']

# 取得父圖 state（包含子圖資訊）
parent_state = parent_graph.get_state(config, subgraphs=True)
print(f"父圖 checkpoint_ns: '{parent_state.config['configurable']['checkpoint_ns']}'")
# 父圖 checkpoint_ns: ''
