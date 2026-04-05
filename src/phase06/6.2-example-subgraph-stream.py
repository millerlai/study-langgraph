# 6.2 範例：子圖串流 - 使用 subgraphs=True
# 展示使用 subgraphs=True 取得子圖的逐步輸出，對比預設不含子圖的串流
"""
子圖串流：使用 subgraphs=True 取得子圖的逐步輸出
"""
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END


class SubState(TypedDict):
    items: Annotated[list[str], add]


class ParentState(TypedDict):
    items: Annotated[list[str], add]
    summary: str


# === 定義子圖 ===
def sub_step_a(state: SubState) -> dict:
    return {"items": ["子圖步驟A完成"]}


def sub_step_b(state: SubState) -> dict:
    return {"items": ["子圖步驟B完成"]}


subgraph = (
    StateGraph(SubState)
    .add_node("step_a", sub_step_a)
    .add_node("step_b", sub_step_b)
    .add_edge(START, "step_a")
    .add_edge("step_a", "step_b")
    .add_edge("step_b", END)
    .compile()
)


# === 定義父圖 ===
def start_node(state: ParentState) -> dict:
    return {"items": ["父圖開始"]}


def end_node(state: ParentState) -> dict:
    return {"summary": f"完成！共 {len(state['items'])} 個步驟"}


parent_graph = (
    StateGraph(ParentState)
    .add_node("start", start_node)
    .add_node("sub", subgraph)        # 子圖作為節點
    .add_node("end", end_node)
    .add_edge(START, "start")
    .add_edge("start", "sub")
    .add_edge("sub", "end")
    .add_edge("end", END)
    .compile()
)

# 啟用 subgraphs=True 來串流子圖的每一步
print("=== 含子圖串流（subgraphs=True） ===")
for namespace, chunk in parent_graph.stream(
    {"items": []},
    stream_mode="updates",
    subgraphs=True,
):
    ns_label = "父圖" if namespace == () else f"子圖({namespace})"
    for node_name, update in chunk.items():
        print(f"  [{ns_label}] {node_name}: {update}")

print()
print("=== 不含子圖串流（預設） ===")
for chunk in parent_graph.stream(
    {"items": []},
    stream_mode="updates",
):
    for node_name, update in chunk.items():
        print(f"  {node_name}: {update}")
