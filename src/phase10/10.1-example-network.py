# 10.1 範例：Multi-Agent Network / Router 模式
# Router 根據問題類型，將請求路由到一個或多個專家 Agent（法律、財務、技術），
# 支援 fan-out/fan-in 平行處理。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# ============================================================
# 1. 定義 State
# ============================================================
class NetworkState(TypedDict):
    question: str
    routes: list[str]                       # 需要諮詢的專家列表
    expert_responses: Annotated[list[str], lambda x, y: x + y]
    final_answer: str
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. Router 節點
# ============================================================
def router(state: NetworkState) -> dict:
    """分析問題，決定需要哪些專家"""
    question = state["question"].lower()
    routes = []

    if any(kw in question for kw in ["法律", "合約", "條款", "法規"]):
        routes.append("legal")
    if any(kw in question for kw in ["財務", "預算", "成本", "費用", "投資"]):
        routes.append("finance")
    if any(kw in question for kw in ["技術", "系統", "架構", "程式", "api"]):
        routes.append("tech")

    if not routes:
        routes = ["tech"]  # 預設路由

    return {
        "routes": routes,
        "logs": [f"[Router] 路由到: {', '.join(routes)}"]
    }


# ============================================================
# 3. 專家 Agent 節點
# ============================================================
def legal_expert(state: NetworkState) -> dict:
    return {
        "expert_responses": [
            f"[法律專家] 針對「{state['question']}」："
            f"從法律角度分析，需注意合規性和風險管理。"
        ],
        "logs": ["[法律專家] 分析完成"]
    }

def finance_expert(state: NetworkState) -> dict:
    return {
        "expert_responses": [
            f"[財務專家] 針對「{state['question']}」："
            f"從財務角度分析，ROI 預估為正，建議控制預算在合理範圍。"
        ],
        "logs": ["[財務專家] 分析完成"]
    }

def tech_expert(state: NetworkState) -> dict:
    return {
        "expert_responses": [
            f"[技術專家] 針對「{state['question']}」："
            f"從技術角度分析，建議採用微服務架構，確保擴展性。"
        ],
        "logs": ["[技術專家] 分析完成"]
    }


# ============================================================
# 4. 結果合併器
# ============================================================
def merge_responses(state: NetworkState) -> dict:
    responses = state.get("expert_responses", [])
    merged = "=== 綜合專家意見 ===\n"
    for resp in responses:
        merged += f"\n{resp}\n"
    merged += f"\n總結：共諮詢了 {len(responses)} 位專家。"
    return {
        "final_answer": merged,
        "logs": ["[合併器] 專家意見已整合"]
    }


# ============================================================
# 5. 條件式路由（fan-out）
# ============================================================
def fan_out_to_experts(state: NetworkState) -> list[Send]:
    """根據 routes 列表，將請求 fan-out 到多個專家"""
    expert_map = {
        "legal": "legal_expert",
        "finance": "finance_expert",
        "tech": "tech_expert"
    }
    sends = []
    for route in state.get("routes", []):
        node_name = expert_map.get(route)
        if node_name:
            sends.append(Send(node_name, state))
    return sends


# ============================================================
# 6. 建立圖
# ============================================================
builder = StateGraph(NetworkState)

builder.add_node("router", router)
builder.add_node("legal_expert", legal_expert)
builder.add_node("finance_expert", finance_expert)
builder.add_node("tech_expert", tech_expert)
builder.add_node("merge", merge_responses)

builder.add_edge(START, "router")

# Fan-out：Router 根據分類結果同時發送到多個專家
builder.add_conditional_edges(
    "router",
    fan_out_to_experts,
    ["legal_expert", "finance_expert", "tech_expert"]
)

# Fan-in：所有專家都匯聚到合併器
builder.add_edge("legal_expert", "merge")
builder.add_edge("finance_expert", "merge")
builder.add_edge("tech_expert", "merge")
builder.add_edge("merge", END)

network_graph = builder.compile()


# ============================================================
# 7. 測試
# ============================================================
# 測試 1：單一路由
print("=== 測試 1：單一專家 ===")
result1 = network_graph.invoke({
    "question": "我們的系統架構需要重構嗎？",
    "routes": [],
    "expert_responses": [],
    "final_answer": "",
    "logs": []
})
for log in result1["logs"]:
    print(f"  {log}")
print(result1["final_answer"])

# 測試 2：多路由
print("\n=== 測試 2：多專家協作 ===")
result2 = network_graph.invoke({
    "question": "評估新系統的技術架構和財務成本",
    "routes": [],
    "expert_responses": [],
    "final_answer": "",
    "logs": []
})
for log in result2["logs"]:
    print(f"  {log}")
print(result2["final_answer"])
