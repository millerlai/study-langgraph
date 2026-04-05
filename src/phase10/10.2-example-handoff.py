# 10.2 範例：Agent Handoff 協作系統
# 兩個 Agent（銷售顧問和技術顧問）透過 Handoff 機制互相轉交控制權。
# 使用 Command + graph=Command.PARENT 實現子圖間的 Handoff。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# ============================================================
# 1. 定義 State
# ============================================================
class ConsultState(TypedDict):
    user_query: str
    active_agent: str
    conversation: Annotated[list[str], lambda x, y: x + y]
    final_answer: str
    handoff_count: int


# ============================================================
# 2. 銷售顧問子圖
# ============================================================
def sales_process(state: ConsultState) -> dict | Command:
    """銷售顧問處理邏輯"""
    query = state["user_query"].lower()

    # 判斷是否需要技術支援
    needs_tech = any(kw in query for kw in ["安裝", "設定", "整合", "api", "技術"])

    if needs_tech and state.get("handoff_count", 0) < 2:
        # Handoff 到技術顧問
        return Command(
            goto="tech_consultant",
            update={
                "active_agent": "tech",
                "handoff_count": state.get("handoff_count", 0) + 1,
                "conversation": [
                    "[銷售顧問] 這個問題涉及技術細節，讓我為您轉接技術顧問。",
                    "[系統] Handoff: 銷售顧問 -> 技術顧問"
                ]
            },
            graph=Command.PARENT
        )
    else:
        return {
            "final_answer": f"[銷售顧問回覆] 關於您的問題「{state['user_query']}」，"
                           f"我們提供三個方案：基礎版、專業版、企業版。",
            "conversation": ["[銷售顧問] 提供產品方案建議"]
        }

sales_builder = StateGraph(ConsultState)
sales_builder.add_node("process", sales_process)
sales_builder.add_edge(START, "process")
sales_builder.add_edge("process", END)
sales_subgraph = sales_builder.compile()


# ============================================================
# 3. 技術顧問子圖
# ============================================================
def tech_process(state: ConsultState) -> dict | Command:
    """技術顧問處理邏輯"""
    query = state["user_query"].lower()

    # 判斷是否需要銷售支援
    needs_sales = any(kw in query for kw in ["價格", "費用", "購買", "方案"])

    if needs_sales and state.get("handoff_count", 0) < 2:
        return Command(
            goto="sales_consultant",
            update={
                "active_agent": "sales",
                "handoff_count": state.get("handoff_count", 0) + 1,
                "conversation": [
                    "[技術顧問] 關於定價問題，讓我為您轉接銷售顧問。",
                    "[系統] Handoff: 技術顧問 -> 銷售顧問"
                ]
            },
            graph=Command.PARENT
        )
    else:
        return {
            "final_answer": f"[技術顧問回覆] 關於「{state['user_query']}」，"
                           f"建議使用 REST API 整合，以下是技術文件連結...",
            "conversation": ["[技術顧問] 提供技術解決方案"]
        }

tech_builder = StateGraph(ConsultState)
tech_builder.add_node("process", tech_process)
tech_builder.add_edge(START, "process")
tech_builder.add_edge("process", END)
tech_subgraph = tech_builder.compile()


# ============================================================
# 4. 父圖
# ============================================================
def route_initial(state: ConsultState) -> Literal["sales_consultant", "tech_consultant"]:
    active = state.get("active_agent", "sales")
    return "tech_consultant" if active == "tech" else "sales_consultant"

def route_after(
    state: ConsultState,
) -> Literal["sales_consultant", "tech_consultant", "__end__"]:
    if state.get("final_answer"):
        return "__end__"
    active = state.get("active_agent", "sales")
    return "tech_consultant" if active == "tech" else "sales_consultant"

parent_builder = StateGraph(ConsultState)
parent_builder.add_node("sales_consultant", sales_subgraph)
parent_builder.add_node("tech_consultant", tech_subgraph)

parent_builder.add_conditional_edges(
    START, route_initial,
    ["sales_consultant", "tech_consultant"]
)
parent_builder.add_conditional_edges(
    "sales_consultant", route_after,
    ["sales_consultant", "tech_consultant", END]
)
parent_builder.add_conditional_edges(
    "tech_consultant", route_after,
    ["sales_consultant", "tech_consultant", END]
)

consult_graph = parent_builder.compile()


# ============================================================
# 5. 測試
# ============================================================
test_queries = [
    {"user_query": "我想了解你們的產品方案", "active_agent": "sales"},
    {"user_query": "如何透過 API 整合你們的系統？", "active_agent": "sales"},
]

for tq in test_queries:
    print(f"--- 問題: {tq['user_query']} ---")
    result = consult_graph.invoke({
        **tq,
        "conversation": [],
        "final_answer": "",
        "handoff_count": 0
    })
    for msg in result["conversation"]:
        print(f"  {msg}")
    print(f"  {result['final_answer']}\n")
