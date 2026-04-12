# 5.2 範例：update_state() 搭配 as_node 參數
# 展示用 as_node 指定以哪個節點身份寫入 State，決定恢復時從哪裡繼續
"""
update_state() 可以用 as_node 參數指定身份，
這決定了恢復時從哪個節點之後繼續
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

class State(TypedDict):
    value: str

def step_a(state: State) -> dict:
    return {"value": state["value"] + " -> A"}

def step_b(state: State) -> dict:
    return {"value": state["value"] + " -> B"}

def step_c(state: State) -> dict:
    return {"value": state["value"] + " -> C"}

builder = StateGraph(State)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_node("step_c", step_c)
builder.add_edge(START, "step_a")
builder.add_edge("step_a", "step_b")
builder.add_edge("step_b", "step_c")
builder.add_edge("step_c", END)

checkpointer = MemorySaver()
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["step_b"],  # step_b 之前暫停
)

config = {"configurable": {"thread_id": "as-node-1"}}

# 執行到 step_a 後暫停（在 step_b 之前）
graph.invoke({"value": "start"}, config=config)
state = graph.get_state(config)
print(f"暫停在 step_b 之前: value={state.values['value']}")
# 暫停在 step_b 之前: value=start -> A

# 用 as_node="step_b" 的身份更新 State
# 這等於「手動執行了 step_b」，恢復時會從 step_c 開始
graph.update_state(
    config,
    values={"value": "start -> A -> B(人類修改)"},
    as_node="step_b",
)

# 恢復 — 直接從 step_c 開始（因為 step_b 已經「被人類執行」了）
result = graph.invoke(Command(resume=True), config=config)
print(f"最終結果: {result['value']}")
# 最終結果: start -> A -> B(人類修改) -> C
