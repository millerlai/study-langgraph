# 3.3 範例：客服工單路由器（基於條件的路由）
# 展示使用確定性規則（關鍵字匹配）將客服工單導向不同處理節點。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義 State
class TicketState(TypedDict):
    user_message: str
    ticket_type: str
    priority: str
    response: str


# 2. 定義 Node 函數
def classify_ticket(state: TicketState) -> dict:
    """基於關鍵字的規則分類"""
    msg = state["user_message"].lower()

    # 規則一：技術問題
    tech_keywords = ["bug", "error", "crash", "無法登入", "當機", "報錯", "壞了"]
    if any(kw in msg for kw in tech_keywords):
        ticket_type = "tech"
        priority = "high"
    # 規則二：帳務問題
    elif any(kw in msg for kw in ["帳單", "付款", "退款", "收費", "billing"]):
        ticket_type = "billing"
        priority = "medium"
    # 規則三：一般問題
    else:
        ticket_type = "general"
        priority = "low"

    print(f"[classify] 類型={ticket_type}, 優先級={priority}")
    return {"ticket_type": ticket_type, "priority": priority}


def handle_tech(state: TicketState) -> dict:
    """技術支援處理"""
    response = (
        f"[技術支援] 收到您的問題：'{state['user_message']}'\n"
        f"優先級：{state['priority']}\n"
        f"我們的工程團隊會在 2 小時內回覆您。"
    )
    print(f"[handle_tech] 處理技術問題")
    return {"response": response}


def handle_billing(state: TicketState) -> dict:
    """帳務問題處理"""
    response = (
        f"[帳務部門] 收到您的問題：'{state['user_message']}'\n"
        f"優先級：{state['priority']}\n"
        f"帳務專員會在 1 個工作天內回覆。"
    )
    print(f"[handle_billing] 處理帳務問題")
    return {"response": response}


def handle_general(state: TicketState) -> dict:
    """一般問題處理"""
    response = (
        f"[客服中心] 收到您的問題：'{state['user_message']}'\n"
        f"優先級：{state['priority']}\n"
        f"我們會盡快回覆您。"
    )
    print(f"[handle_general] 處理一般問題")
    return {"response": response}


def send_response(state: TicketState) -> dict:
    """發送回應"""
    print(f"[send_response] 回應已發送")
    return {}


# 3. 路由函數
def route_ticket(state: TicketState) -> str:
    """根據工單類型路由"""
    routes = {
        "tech": "handle_tech",
        "billing": "handle_billing",
        "general": "handle_general",
    }
    return routes.get(state["ticket_type"], "handle_general")


# 4. 建構 Graph
builder = StateGraph(TicketState)
builder.add_node("classify", classify_ticket)
builder.add_node("handle_tech", handle_tech)
builder.add_node("handle_billing", handle_billing)
builder.add_node("handle_general", handle_general)
builder.add_node("send_response", send_response)

builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",
    route_ticket,
    ["handle_tech", "handle_billing", "handle_general"]
)
builder.add_edge("handle_tech", "send_response")
builder.add_edge("handle_billing", "send_response")
builder.add_edge("handle_general", "send_response")
builder.add_edge("send_response", END)

graph = builder.compile()

# 5. 測試
test_cases = [
    "我的帳號無法登入，一直報錯",
    "上個月的帳單好像多收了費用",
    "請問你們的營業時間是幾點？",
]

for msg in test_cases:
    print(f"\n{'='*50}")
    print(f"使用者: {msg}")
    result = graph.invoke({
        "user_message": msg,
        "ticket_type": "",
        "priority": "",
        "response": "",
    })
    print(f"\n{result['response']}")
