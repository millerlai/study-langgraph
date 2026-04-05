# 9.2 範例：子圖間透過 Command 直接傳遞資料
# 子圖 A（前端 Agent）透過 Command 導航到子圖 B（後端 Agent），並攜帶上下文資料。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# ============================================================
# 1. 共享 State
# ============================================================
class HandoffState(TypedDict):
    message: str
    context: dict           # 傳遞的上下文資料
    response: str
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. 子圖 A：前端 Agent
# ============================================================
def receive_request(state: HandoffState) -> dict:
    return {"logs": [f"[前端] 收到請求: {state['message']}"]}

def handoff_to_backend(state: HandoffState) -> Command:
    """透過 Command 直接導航到子圖 B，攜帶上下文"""
    return Command(
        goto="backend_agent",
        update={
            "context": {
                "original_message": state["message"],
                "priority": "high",
                "processed_by": "frontend_agent"
            },
            "logs": ["[前端 -> 後端] Handoff，附帶上下文資料"]
        },
        graph=Command.PARENT
    )

frontend_builder = StateGraph(HandoffState)
frontend_builder.add_node("receive", receive_request)
frontend_builder.add_node("handoff", handoff_to_backend)
frontend_builder.add_edge(START, "receive")
frontend_builder.add_edge("receive", "handoff")
frontend_subgraph = frontend_builder.compile()


# ============================================================
# 3. 子圖 B：後端 Agent
# ============================================================
def process_request(state: HandoffState) -> dict:
    """讀取從子圖 A 傳遞過來的 context"""
    ctx = state.get("context", {})
    original = ctx.get("original_message", "unknown")
    priority = ctx.get("priority", "normal")
    return {
        "response": f"已處理（優先級: {priority}）: {original}",
        "logs": [f"[後端] 處理完成，優先級: {priority}"]
    }

backend_builder = StateGraph(HandoffState)
backend_builder.add_node("process", process_request)
backend_builder.add_edge(START, "process")
backend_builder.add_edge("process", END)
backend_subgraph = backend_builder.compile()


# ============================================================
# 4. 父圖
# ============================================================
parent_builder = StateGraph(HandoffState)
parent_builder.add_node("frontend_agent", frontend_subgraph)
parent_builder.add_node("backend_agent", backend_subgraph)
parent_builder.add_edge(START, "frontend_agent")
# frontend 透過 Command 導航到 backend，不需要靜態 edge
parent_builder.add_edge("backend_agent", END)

parent_graph = parent_builder.compile()


# ============================================================
# 5. 執行
# ============================================================
result = parent_graph.invoke({
    "message": "請幫我建立一個新的專案",
    "context": {},
    "response": "",
    "logs": []
})

print("=== 日誌 ===")
for log in result["logs"]:
    print(f"  {log}")
print(f"\n最終回應: {result['response']}")
print(f"上下文: {result['context']}")
