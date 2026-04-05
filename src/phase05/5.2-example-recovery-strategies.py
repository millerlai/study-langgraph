# 5.2 範例：多種恢復策略（接受/拒絕/修改）
# 展示中斷後的三種恢復方式：accept、reject、自定義修改
"""
多種恢復策略的完整範例
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import operator

class State(TypedDict):
    task: str
    attempts: Annotated[list[str], operator.add]
    result: str

def process(state: State) -> dict:
    """處理任務，需要人類確認"""
    task = state["task"]
    decision = interrupt({
        "message": f"即將處理任務：{task}",
        "options": ["accept", "reject", "retry"],
    })

    if decision == "accept":
        return {
            "result": f"任務「{task}」已完成",
            "attempts": [f"處理完成: {task}"],
        }
    elif decision == "reject":
        return {
            "result": f"任務「{task}」已被取消",
            "attempts": [f"任務被拒絕: {task}"],
        }
    else:
        return {
            "result": f"任務已按照新指示處理: {decision}",
            "attempts": [f"重試: {decision}"],
        }

builder = StateGraph(State)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 策略 1: 接受 ===
print("=== 策略 1: 接受 ===")
config1 = {"configurable": {"thread_id": "strategy-accept"}}
graph.invoke({"task": "部署新版本", "attempts": [], "result": ""}, config=config1)
result = graph.invoke(Command(resume="accept"), config=config1)
print(f"結果: {result['result']}")
# 結果: 任務「部署新版本」已完成

# === 策略 2: 拒絕 ===
print("\n=== 策略 2: 拒絕 ===")
config2 = {"configurable": {"thread_id": "strategy-reject"}}
graph.invoke({"task": "刪除測試環境", "attempts": [], "result": ""}, config=config2)
result = graph.invoke(Command(resume="reject"), config=config2)
print(f"結果: {result['result']}")
# 結果: 任務「刪除測試環境」已被取消

# === 策略 3: 修改後重試 ===
print("\n=== 策略 3: 修改後重試 ===")
config3 = {"configurable": {"thread_id": "strategy-retry"}}
graph.invoke({"task": "備份資料庫", "attempts": [], "result": ""}, config=config3)
result = graph.invoke(Command(resume="改為增量備份"), config=config3)
print(f"結果: {result['result']}")
# 結果: 任務已按照新指示處理: 改為增量備份
