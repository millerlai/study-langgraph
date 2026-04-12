# 5.1 範例：動態 Breakpoint (NodeInterrupt)
# 展示使用 NodeInterrupt 例外在節點中根據條件拋出中斷
"""
動態 Breakpoint：用 NodeInterrupt 條件性地中斷
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt
from langgraph.types import Command

class State(TypedDict):
    amount: int
    approved: bool
    result: str

def check_and_process(state: State) -> dict:
    """檢查金額——超過閾值時拋出 NodeInterrupt"""
    amount = state["amount"]

    if amount > 10000:
        # 動態 Breakpoint：根據條件拋出
        raise NodeInterrupt(
            f"金額 ${amount:,} 超過 $10,000 限額，需要主管批准"
        )

    return {"result": f"已處理 ${amount:,} 的交易", "approved": True}

builder = StateGraph(State)
builder.add_node("check_and_process", check_and_process)
builder.add_edge(START, "check_and_process")
builder.add_edge("check_and_process", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# --- 測試小金額（不會中斷）---
config_small = {"configurable": {"thread_id": "small-amount"}}
result = graph.invoke(
    {"amount": 5000, "approved": False, "result": ""},
    config=config_small,
)
print(f"小金額: {result['result']}")
# 小金額: 已處理 $5,000 的交易

# --- 測試大金額（會中斷）---
config_large = {"configurable": {"thread_id": "large-amount"}}
result = graph.invoke(
    {"amount": 50000, "approved": False, "result": ""},
    config=config_large,
)

state = graph.get_state(config_large)
print(f"\n大金額 — 暫停在: {state.next}")
# 大金額 — 暫停在: ('check_and_process',)

# 恢復時，NodeInterrupt 的節點會「重新執行」
# 需要先修改 State 讓條件不再觸發，或用 update 修改
result = graph.invoke(
    Command(resume=True, update={"amount": 8000}),
    config=config_large,
)
print(f"修改後結果: {result['result']}")
# 修改後結果: 已處理 $8,000 的交易
