# 9.2 範例：多子圖協作系統 — 客服工單處理管線
# Classifier 分析工單後透過 Command 導航到對應 Agent（技術支援或帳務），
# 各 Agent 處理完後透過 Command 導航到 Summarizer。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# ============================================================
# 1. 定義 State
# ============================================================
class TicketState(TypedDict):
    ticket_content: str                     # 工單內容
    category: str                           # 分類結果
    resolution: str                         # 處理結果
    summary: str                            # 最終摘要
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. 子圖：分類 Agent
# ============================================================
def classify_ticket(state: TicketState) -> dict:
    content = state.get("ticket_content", "").lower()
    if any(kw in content for kw in ["密碼", "登入", "錯誤", "bug", "當機"]):
        category = "technical"
    elif any(kw in content for kw in ["帳單", "付款", "退款", "費用", "訂閱"]):
        category = "billing"
    else:
        category = "technical"  # 預設歸類為技術支援
    return {
        "category": category,
        "logs": [f"[分類] 工單分類為: {category}"]
    }

def route_to_agent(state: TicketState) -> Command:
    """根據分類結果導航到對應的 Agent"""
    category = state.get("category", "technical")
    target = "tech_support" if category == "technical" else "billing"
    return Command(
        goto=target,
        update={
            "logs": [f"[分類 -> {target}] 轉派工單"]
        },
        graph=Command.PARENT
    )

classifier_builder = StateGraph(TicketState)
classifier_builder.add_node("classify", classify_ticket)
classifier_builder.add_node("route", route_to_agent)
classifier_builder.add_edge(START, "classify")
classifier_builder.add_edge("classify", "route")
classifier_subgraph = classifier_builder.compile()


# ============================================================
# 3. 子圖：技術支援 Agent
# ============================================================
def diagnose_issue(state: TicketState) -> dict:
    return {
        "resolution": f"技術診斷: 針對 '{state['ticket_content']}' 的問題已找到解決方案",
        "logs": ["[技術支援] 問題診斷完成"]
    }

def nav_to_summary_tech(state: TicketState) -> Command:
    return Command(
        goto="summarizer",
        update={"logs": ["[技術支援 -> 摘要] 處理完成"]},
        graph=Command.PARENT
    )

tech_builder = StateGraph(TicketState)
tech_builder.add_node("diagnose", diagnose_issue)
tech_builder.add_node("nav", nav_to_summary_tech)
tech_builder.add_edge(START, "diagnose")
tech_builder.add_edge("diagnose", "nav")
tech_subgraph = tech_builder.compile()


# ============================================================
# 4. 子圖：帳務 Agent
# ============================================================
def process_billing(state: TicketState) -> dict:
    return {
        "resolution": f"帳務處理: 針對 '{state['ticket_content']}' 已完成帳務審核",
        "logs": ["[帳務] 帳務審核完成"]
    }

def nav_to_summary_billing(state: TicketState) -> Command:
    return Command(
        goto="summarizer",
        update={"logs": ["[帳務 -> 摘要] 處理完成"]},
        graph=Command.PARENT
    )

billing_builder = StateGraph(TicketState)
billing_builder.add_node("process", process_billing)
billing_builder.add_node("nav", nav_to_summary_billing)
billing_builder.add_edge(START, "process")
billing_builder.add_edge("process", "nav")
billing_subgraph = billing_builder.compile()


# ============================================================
# 5. 父圖的摘要節點
# ============================================================
def create_summary(state: TicketState) -> dict:
    return {
        "summary": (
            f"工單摘要\n"
            f"  內容: {state['ticket_content']}\n"
            f"  分類: {state['category']}\n"
            f"  結果: {state['resolution']}"
        ),
        "logs": ["[摘要] 工單摘要已生成"]
    }


# ============================================================
# 6. 建立父圖
# ============================================================
parent_builder = StateGraph(TicketState)
parent_builder.add_node("classifier", classifier_subgraph)
parent_builder.add_node("tech_support", tech_subgraph)
parent_builder.add_node("billing", billing_subgraph)
parent_builder.add_node("summarizer", create_summary)

parent_builder.add_edge(START, "classifier")
# classifier, tech_support, billing 的路由由 Command 處理
parent_builder.add_edge("summarizer", END)

parent_graph = parent_builder.compile()


# ============================================================
# 7. 測試
# ============================================================
print("=== 測試 1：技術問題 ===")
result1 = parent_graph.invoke({
    "ticket_content": "我的帳號登入時出現錯誤代碼 500",
    "category": "",
    "resolution": "",
    "summary": "",
    "logs": []
})
for log in result1["logs"]:
    print(f"  {log}")
print(f"\n{result1['summary']}")

print("\n" + "=" * 50)

print("\n=== 測試 2：帳務問題 ===")
result2 = parent_graph.invoke({
    "ticket_content": "我要申請上個月的退款",
    "category": "",
    "resolution": "",
    "summary": "",
    "logs": []
})
for log in result2["logs"]:
    print(f"  {log}")
print(f"\n{result2['summary']}")
