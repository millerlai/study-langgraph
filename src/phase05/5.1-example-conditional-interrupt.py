# 5.1 範例：條件式 interrupt()
# 展示只在特定條件下（高風險操作）才暫停的中斷模式
"""
條件式 interrupt()：只在特定條件下暫停
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    action: str
    risk_level: str
    approved: bool
    result: str

def evaluate_risk(state: State) -> dict:
    """評估操作風險"""
    action = state["action"]
    if "delete" in action.lower() or "drop" in action.lower():
        return {"risk_level": "high"}
    return {"risk_level": "low"}

def execute_action(state: State) -> dict:
    """執行操作——高風險需要人類批准"""
    if state["risk_level"] == "high":
        # 只在高風險時中斷
        approval = interrupt({
            "message": f"高風險操作需要審核：{state['action']}",
            "risk_level": state["risk_level"],
        })
        if approval != "approved":
            return {"result": "操作已被拒絕", "approved": False}

    return {"result": f"操作「{state['action']}」已執行完成", "approved": True}

# 建構 Graph
builder = StateGraph(State)
builder.add_node("evaluate_risk", evaluate_risk)
builder.add_node("execute_action", execute_action)
builder.add_edge(START, "evaluate_risk")
builder.add_edge("evaluate_risk", "execute_action")
builder.add_edge("execute_action", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# --- 測試低風險操作（不會暫停）---
config_low = {"configurable": {"thread_id": "low-risk-1"}}
result = graph.invoke({"action": "查詢使用者列表", "risk_level": "", "approved": False, "result": ""}, config=config_low)
print(f"低風險結果: {result['result']}")
# 低風險結果: 操作「查詢使用者列表」已執行完成

# --- 測試高風險操作（會暫停）---
config_high = {"configurable": {"thread_id": "high-risk-1"}}
result = graph.invoke({"action": "DELETE 所有資料", "risk_level": "", "approved": False, "result": ""}, config=config_high)
print(f"\n高風險 — 暫停後的 State: next={graph.get_state(config_high).next}")
# 高風險 — 暫停後的 State: next=('execute_action',)

# 批准操作
result = graph.invoke(Command(resume="approved"), config=config_high)
print(f"高風險結果: {result['result']}")
# 高風險結果: 操作「DELETE 所有資料」已執行完成
