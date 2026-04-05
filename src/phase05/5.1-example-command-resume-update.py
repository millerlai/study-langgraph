# 5.1 範例：Command 進階用法 - resume + update 同時操作
# 展示恢復執行時同時更新 State 中的欄位
"""
Command 進階用法：resume + update 同時操作
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import operator

class State(TypedDict):
    task: str
    logs: Annotated[list[str], operator.add]
    priority: str
    result: str

def process_task(state: State) -> dict:
    """處理任務——中斷等待確認"""
    feedback = interrupt(f"任務「{state['task']}」準備執行，請確認或修改優先級")
    return {
        "result": f"以 {state['priority']} 優先級完成任務",
        "logs": [f"收到人類回饋: {feedback}"],
    }

builder = StateGraph(State)
builder.add_node("process_task", process_task)
builder.add_edge(START, "process_task")
builder.add_edge("process_task", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "cmd-1"}}

# 第一次呼叫
graph.invoke(
    {"task": "部署到正式環境", "logs": ["任務建立"], "priority": "medium", "result": ""},
    config=config,
)

# 恢復時同時更新 State 中的 priority
result = graph.invoke(
    Command(
        resume="已確認，提升優先級",
        update={"priority": "high", "logs": ["人類提升優先級為 high"]},
    ),
    config=config,
)

print(f"結果: {result['result']}")
print(f"日誌: {result['logs']}")
# 結果: 以 high 優先級完成任務
# 日誌: ['任務建立', '人類提升優先級為 high', '收到人類回饋: 已確認，提升優先級']
