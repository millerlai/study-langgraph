# 1.1 LangGraph 概觀 — 最小完整範例
# 展示 LangGraph 最基本的用法：定義 State、Node、Edge，建構並執行 Graph
# 不需要 API key

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

# 1. 定義 State
class MyState(TypedDict):
    counter: int
    message: str

# 2. 定義 Node
def increment(state: MyState) -> dict:
    return {"counter": state["counter"] + 1, "message": "已加一"}

def double(state: MyState) -> dict:
    return {"counter": state["counter"] * 2, "message": "已加倍"}

# 3. 建構 Graph
builder = StateGraph(MyState)
builder.add_node("increment", increment)
builder.add_node("double", double)
builder.add_edge(START, "increment")
builder.add_edge("increment", "double")
builder.add_edge("double", END)

graph = builder.compile()

# 4. 執行
result = graph.invoke({"counter": 3, "message": ""})
print(result)
# {'counter': 8, 'message': '已加倍'}
# 流程：3 → increment(+1) → 4 → double(×2) → 8
