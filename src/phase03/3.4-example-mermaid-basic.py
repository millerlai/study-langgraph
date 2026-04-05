# 3.4 範例：基本 Mermaid 輸出
# 展示將編譯後的圖結構輸出為 Mermaid 格式文字。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義一個有條件分支的 Graph
class State(TypedDict):
    value: int
    result: str


def step_a(state: State) -> dict:
    return {"value": state["value"] + 1}


def step_b(state: State) -> dict:
    return {"result": "走了 B 路線"}


def step_c(state: State) -> dict:
    return {"result": "走了 C 路線"}


def route(state: State) -> str:
    if state["value"] > 5:
        return "step_b"
    return "step_c"


builder = StateGraph(State)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_node("step_c", step_c)

builder.add_edge(START, "step_a")
builder.add_conditional_edges("step_a", route, ["step_b", "step_c"])
builder.add_edge("step_b", END)
builder.add_edge("step_c", END)

graph = builder.compile()

# 2. 輸出 Mermaid 語法
mermaid_text = graph.get_graph().draw_mermaid()
print(mermaid_text)
