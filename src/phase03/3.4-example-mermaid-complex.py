# 3.4 範例：複雜圖的 Mermaid 輸出
# 展示包含迴圈、分支、平行的複雜圖結構的 Mermaid 輸出與結構資訊。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import operator


# 一個包含迴圈、分支、平行的複雜圖
class ComplexState(TypedDict):
    messages: Annotated[list[str], operator.add]
    step_count: int


def entry_node(state: ComplexState) -> dict:
    return {"messages": ["進入"], "step_count": 0}


def process_a(state: ComplexState) -> dict:
    return {"messages": ["處理 A"]}


def process_b(state: ComplexState) -> dict:
    return {"messages": ["處理 B"]}


def check_node(state: ComplexState) -> Command[Literal["process_a", "__end__"]]:
    count = state["step_count"] + 1
    if count >= 3:
        return Command(update={"step_count": count}, goto=END)
    return Command(update={"step_count": count}, goto="process_a")


builder = StateGraph(ComplexState)
builder.add_node("entry_node", entry_node)
builder.add_node("process_a", process_a)
builder.add_node("process_b", process_b)
builder.add_node("check_node", check_node)

builder.add_edge(START, "entry_node")
# entry_node 同時連到 process_a 和 process_b（平行）
builder.add_edge("entry_node", "process_a")
builder.add_edge("entry_node", "process_b")
# 兩個分支都連到 check_node
builder.add_edge("process_a", "check_node")
builder.add_edge("process_b", "check_node")
# check_node 透過 Command 決定是迴圈還是結束

graph = builder.compile()

# 輸出 Mermaid
print("=== Mermaid 圖表 ===")
print(graph.get_graph().draw_mermaid())

# 也可以輸出為 ASCII（取得圖的節點和邊資訊）
print("\n=== 圖結構資訊 ===")
drawable = graph.get_graph()
print(f"節點: {list(drawable.nodes)}")
print(f"邊數: {len(drawable.edges)}")
for edge in drawable.edges:
    edge_type = "條件" if edge.conditional else "固定"
    print(f"  {edge.source} --({edge_type})--> {edge.target}")
