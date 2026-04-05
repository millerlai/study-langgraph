# 3.2 範例：主動式遞迴處理（使用 RemainingSteps）
# 展示使用 RemainingSteps managed value 主動監控剩餘步數，實現優雅收尾。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.managed import RemainingSteps


# 1. 定義 State（包含 RemainingSteps）
class SmartState(TypedDict):
    messages: Annotated[list[str], lambda x, y: x + y]
    remaining_steps: RemainingSteps  # 由 LangGraph 自動管理


# 2. 定義 Node
def agent_node(state: SmartState) -> dict:
    """Agent 節點：監控剩餘步數"""
    remaining = state["remaining_steps"]
    step_msg = f"處理中... (剩餘步數: {remaining})"
    print(f"[agent_node] {step_msg}")

    if remaining <= 2:
        # 剩餘步數不夠，提早收尾
        return {"messages": ["接近限制，提供目前最佳結果。"]}

    return {"messages": [step_msg]}


def route_decision(state: SmartState) -> str:
    """基於剩餘步數決定是否繼續"""
    if state["remaining_steps"] <= 2:
        return END
    # 模擬：有 messages 超過 3 條就停止
    if len(state["messages"]) >= 3:
        return END
    return "agent_node"


# 3. 建構 Graph
builder = StateGraph(SmartState)
builder.add_node("agent_node", agent_node)

builder.add_edge(START, "agent_node")
builder.add_conditional_edges("agent_node", route_decision)

graph = builder.compile()

# 4. 執行：設定較低的 recursion_limit 來觀察效果
result = graph.invoke(
    {"messages": []},
    config={"recursion_limit": 8}
)

print(f"\n最終 messages:")
for msg in result["messages"]:
    print(f"  - {msg}")
