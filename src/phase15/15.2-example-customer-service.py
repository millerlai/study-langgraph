# 15.2 範例：客服 Agent 完整開發流程
# 包含工具、人工審核（interrupt）、條件路由
# 搭配 langgraph.json 使用，用 langgraph dev 啟動後可在 Studio 中操作
# 需要：pip install langgraph langchain-openai langchain-core
# 需要：設定 OPENAI_API_KEY 環境變數

from typing import Literal
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import interrupt, Command


# === 工具 ===
@tool
def lookup_order(order_id: str) -> str:
    """查詢訂單狀態"""
    orders = {
        "ORD-001": "已出貨，預計明天送達",
        "ORD-002": "處理中，預計 3 天內出貨",
    }
    return orders.get(order_id, f"找不到訂單 {order_id}")


@tool
def create_ticket(issue: str, priority: str = "normal") -> str:
    """建立客服工單"""
    return f"已建立工單 TK-{hash(issue) % 10000:04d}（優先度：{priority}）"


tools = [lookup_order, create_ticket]
tool_node = ToolNode(tools)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)


# === State ===
class CustomerServiceState(MessagesState):
    needs_escalation: bool


# === Nodes ===
def agent(state: CustomerServiceState) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def check_escalation(
    state: CustomerServiceState,
) -> Command[Literal["tools", "human_review", "__end__"]]:
    last_msg = state["messages"][-1]

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return Command(goto="tools")

    # 檢查是否需要人工介入
    content = getattr(last_msg, "content", "")
    if "退款" in content or "投訴" in content:
        return Command(
            update={"needs_escalation": True},
            goto="human_review",
        )
    return Command(goto="__end__")


def human_review(state: CustomerServiceState) -> dict:
    """人工審核節點 — 在 Studio 中會暫停等待輸入"""
    decision = interrupt({
        "message": "此對話需要人工審核",
        "conversation": [
            getattr(m, "content", str(m)) for m in state["messages"][-3:]
        ],
        "action": "請決定如何處理（approve / escalate / reject）",
    })

    if decision.get("action") == "approve":
        return {
            "messages": [
                {"role": "assistant", "content": "您的請求已獲得核准，我們會盡快處理。"}
            ]
        }
    elif decision.get("action") == "escalate":
        return {
            "messages": [
                {"role": "assistant", "content": "已將您的問題轉交給資深客服人員。"}
            ]
        }
    return {
        "messages": [
            {"role": "assistant", "content": "感謝您的耐心，我們正在處理您的請求。"}
        ]
    }


# === 建構 Graph ===
workflow = StateGraph(CustomerServiceState)
workflow.add_node("agent", agent)
workflow.add_node("check_escalation", check_escalation)
workflow.add_node("tools", tool_node)
workflow.add_node("human_review", human_review)

workflow.add_edge(START, "agent")
workflow.add_edge("agent", "check_escalation")
workflow.add_edge("tools", "agent")
workflow.add_edge("human_review", END)

graph = workflow.compile()
