# 1.1 LangGraph 概觀 — Human-in-the-Loop 審核範例
# 展示如何使用 interrupt() 暫停執行，讓人類審核後再繼續
# 不需要 API key

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

# 1. 定義 State
class MyState(TypedDict):
    request: str       # 使用者的請求
    result: str        # 最終結果
    approved: bool     # 是否通過審核

# 2. 定義 Nodes
def analyze_request(state: MyState) -> dict:
    """分析使用者請求，判斷要執行什麼操作"""
    request = state["request"]
    return {"result": f"準備執行：{request}"}

def sensitive_action(state: MyState) -> dict:
    """執行敏感操作前，先暫停讓人類審核"""
    # interrupt() 會暫停整個 graph，等待人類回應
    # 傳入的字串是給人類看的提示訊息
    human_decision = interrupt(
        f"⚠️ 即將執行敏感操作：{state['result']}\n"
        f"請輸入 'approved' 核准，或其他任意值拒絕。"
    )

    if human_decision == "approved":
        return {
            "result": f"✅ 已執行：{state['request']}",
            "approved": True,
        }
    else:
        return {
            "result": f"❌ 已取消：{state['request']}",
            "approved": False,
        }

def report(state: MyState) -> dict:
    """產生最終報告"""
    status = "核准並執行" if state["approved"] else "已被拒絕"
    return {"result": f"最終結果 — {status}：{state['result']}"}

# 3. 建構 Graph
builder = StateGraph(MyState)
builder.add_node("analyze", analyze_request)
builder.add_node("sensitive", sensitive_action)   # 這個節點會暫停
builder.add_node("report", report)

builder.add_edge(START, "analyze")
builder.add_edge("analyze", "sensitive")
builder.add_edge("sensitive", "report")
builder.add_edge("report", END)

# 4. 編譯時必須指定 checkpointer（interrupt 需要持久化狀態）
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 5. 執行——會在 sensitive_action 的 interrupt() 處暫停
config = {"configurable": {"thread_id": "review-001"}}
result = graph.invoke(
    {"request": "刪除所有過期使用者", "result": "", "approved": False},
    config,
)
print(result)
# 此時 graph 暫停，result 會包含到目前為止的 state

# 6. 人類審核後，用 Command(resume=...) 恢復執行
result = graph.invoke(
    Command(resume="approved"),   # 將 "approved" 傳回給 interrupt()
    config,                       # 同一個 thread_id，接續上次的執行
)
print(result)
# {'request': '刪除所有過期使用者', 'result': '最終結果 — 核准並執行：...', 'approved': True}
