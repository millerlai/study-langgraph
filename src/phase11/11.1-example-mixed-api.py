# 11.1 範例：混合使用 Graph API 與 Functional API
# 示範在 Functional API 工作流中呼叫 Graph API 子圖

import uuid
from typing import TypedDict
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

# ============================================================
# 1. 用 Graph API 建立一個子圖
# ============================================================
class MathState(TypedDict):
    value: int

def triple(state: MathState) -> MathState:
    return {"value": state["value"] * 3}

builder = StateGraph(MathState)
builder.add_node("triple", triple)
builder.set_entry_point("triple")
math_graph = builder.compile()

# ============================================================
# 2. 用 Functional API 建立主工作流，內部呼叫子圖
# ============================================================
checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def main_workflow(x: int) -> dict:
    """Functional API 呼叫 Graph API 子圖"""
    graph_result = math_graph.invoke({"value": x})
    doubled = graph_result["value"] * 2
    return {
        "original": x,
        "tripled": graph_result["value"],
        "then_doubled": doubled
    }

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = main_workflow.invoke(5, config=config)
print(result)
# 輸出: {'original': 5, 'tripled': 15, 'then_doubled': 30}
