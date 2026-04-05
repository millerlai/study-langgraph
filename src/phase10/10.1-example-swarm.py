# 10.1 範例：Swarm 模式（去中心化協調）
# 三個 Agent（銷售、客服、技術）組成 Swarm，每個 Agent 可根據對話內容自主 handoff。
# 使用 LangGraph StateGraph + Command 實現。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# ============================================================
# 1. 定義 State
# ============================================================
class SwarmState(TypedDict):
    message: str                            # 用戶訊息
    active_agent: str                       # 目前活躍的 Agent
    response: str                           # 最終回應
    handoff_count: int                      # Handoff 次數
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. 銷售 Agent
# ============================================================
def sales_agent(state: SwarmState) -> dict | Command:
    """
    銷售 Agent：處理銷售相關問題。
    如果遇到技術問題，handoff 給技術 Agent。
    如果遇到帳務問題，handoff 給客服 Agent。
    """
    message = state["message"].lower()
    handoffs = state.get("handoff_count", 0)

    # 防止無限 handoff
    if handoffs >= 3:
        return {
            "response": "[銷售] 已超過轉接上限，直接回覆：感謝您的詢問，我們會盡快安排專人聯繫。",
            "logs": ["[銷售] 達到 handoff 上限，直接回覆"]
        }

    if any(kw in message for kw in ["bug", "錯誤", "當機", "技術"]):
        return Command(
            goto="tech_agent",
            update={
                "active_agent": "tech",
                "handoff_count": handoffs + 1,
                "logs": ["[銷售 -> 技術] Handoff：偵測到技術問題"]
            }
        )
    elif any(kw in message for kw in ["退款", "帳單", "付款"]):
        return Command(
            goto="service_agent",
            update={
                "active_agent": "service",
                "handoff_count": handoffs + 1,
                "logs": ["[銷售 -> 客服] Handoff：偵測到帳務問題"]
            }
        )
    else:
        return {
            "response": f"[銷售回覆] 感謝您的詢問！關於「{state['message']}」，我們目前有優惠方案...",
            "logs": ["[銷售] 處理完成，直接回覆"]
        }


# ============================================================
# 3. 客服 Agent
# ============================================================
def service_agent(state: SwarmState) -> dict | Command:
    """
    客服 Agent：處理帳務和一般客服問題。
    如果遇到技術問題，handoff 給技術 Agent。
    """
    message = state["message"].lower()
    handoffs = state.get("handoff_count", 0)

    if handoffs >= 3:
        return {
            "response": "[客服] 已超過轉接上限，已為您建立工單，專人會在 24 小時內回覆。",
            "logs": ["[客服] 達到 handoff 上限，直接回覆"]
        }

    if any(kw in message for kw in ["bug", "錯誤", "當機"]):
        return Command(
            goto="tech_agent",
            update={
                "active_agent": "tech",
                "handoff_count": handoffs + 1,
                "logs": ["[客服 -> 技術] Handoff：偵測到技術問題"]
            }
        )
    else:
        return {
            "response": f"[客服回覆] 您好！關於「{state['message']}」，我已查詢您的帳戶狀態...",
            "logs": ["[客服] 處理完成，直接回覆"]
        }


# ============================================================
# 4. 技術 Agent
# ============================================================
def tech_agent(state: SwarmState) -> dict:
    """
    技術 Agent：處理技術問題，不再 handoff。
    """
    return {
        "response": f"[技術回覆] 關於「{state['message']}」，我已排查問題，以下是解決方案：\n"
                   f"  1. 清除快取\n"
                   f"  2. 重新啟動服務\n"
                   f"  3. 如仍有問題，請提供日誌",
        "logs": ["[技術] 問題排查完成，回覆解決方案"]
    }


# ============================================================
# 5. 路由函式
# ============================================================
def route_after_agent(
    state: SwarmState,
) -> Literal["sales_agent", "service_agent", "tech_agent", "__end__"]:
    """判斷是否需要繼續路由或結束"""
    if state.get("response"):
        return "__end__"
    # 根據 active_agent 路由
    active = state.get("active_agent", "sales")
    agent_map = {
        "sales": "sales_agent",
        "service": "service_agent",
        "tech": "tech_agent"
    }
    return agent_map.get(active, "sales_agent")

def initial_route(state: SwarmState) -> Literal["sales_agent", "service_agent", "tech_agent"]:
    """初始路由"""
    active = state.get("active_agent", "sales")
    agent_map = {
        "sales": "sales_agent",
        "service": "service_agent",
        "tech": "tech_agent"
    }
    return agent_map.get(active, "sales_agent")


# ============================================================
# 6. 建立圖
# ============================================================
builder = StateGraph(SwarmState)

builder.add_node("sales_agent", sales_agent)
builder.add_node("service_agent", service_agent)
builder.add_node("tech_agent", tech_agent)

builder.add_conditional_edges(
    START, initial_route,
    ["sales_agent", "service_agent", "tech_agent"]
)

# 每個 Agent 執行後檢查是否結束或繼續路由
for agent_name in ["sales_agent", "service_agent", "tech_agent"]:
    builder.add_conditional_edges(
        agent_name,
        route_after_agent,
        ["sales_agent", "service_agent", "tech_agent", END]
    )

swarm_graph = builder.compile()


# ============================================================
# 7. 測試
# ============================================================
test_cases = [
    {"message": "我想了解你們的產品方案", "active_agent": "sales"},
    {"message": "我的帳單有問題，想申請退款", "active_agent": "sales"},
    {"message": "系統登入時一直出現錯誤", "active_agent": "service"},
]

for tc in test_cases:
    print(f"--- 訊息: {tc['message']} ---")
    result = swarm_graph.invoke({
        **tc,
        "response": "",
        "handoff_count": 0,
        "logs": []
    })
    for log in result["logs"]:
        print(f"  {log}")
    print(f"  回應: {result['response']}\n")
