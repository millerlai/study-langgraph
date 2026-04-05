# 16.2 範例：主動式 Recursion Limit 處理
# 使用 RemainingSteps 在接近限制時優雅降級
# 需要：pip install langgraph

from typing import Annotated, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.managed import RemainingSteps


class State(TypedDict):
    messages: Annotated[list[str], lambda x, y: x + y]
    remaining_steps: RemainingSteps  # 自動追蹤剩餘步數


def reasoning_node(state: State) -> dict:
    """推理節點：根據剩餘步數調整行為"""
    remaining = state["remaining_steps"]
    print(f"  剩餘步數: {remaining}")

    if remaining <= 2:
        # 快要到限制了，直接給出最佳答案
        return {"messages": ["[接近限制] 根據目前資訊，這是我的最佳回答..."]}

    # 正常處理
    return {"messages": ["讓我再想想..."]}


def route(state: State) -> Literal["reasoning_node", "fallback"]:
    """路由：根據剩餘步數決定下一步"""
    if state["remaining_steps"] <= 2:
        return "fallback"
    return "reasoning_node"


def fallback(state: State) -> dict:
    """降級節點：在限制內完成"""
    return {"messages": ["[降級] 已達到複雜度限制，提供最佳近似答案。"]}


builder = StateGraph(State)
builder.add_node("reasoning_node", reasoning_node)
builder.add_node("fallback", fallback)
builder.add_edge(START, "reasoning_node")
builder.add_conditional_edges("reasoning_node", route)
builder.add_edge("fallback", END)

graph = builder.compile()

# RemainingSteps 與 recursion_limit 搭配使用
result = graph.invoke(
    {"messages": ["開始推理"]},
    config={"recursion_limit": 10},
)
print(f"結果: {result['messages']}")
