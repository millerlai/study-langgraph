# 5.1 範例：靜態 Breakpoint (interrupt_before)
# 展示在 compile() 時設定 interrupt_before，不需要修改節點程式碼
"""
靜態 Breakpoint：在 compile() 時設定，不需要修改節點程式碼
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

class State(TypedDict):
    data: str
    validated: bool
    processed: str

def fetch_data(state: State) -> dict:
    """取得資料"""
    return {"data": "從 API 取得的原始資料"}

def validate_data(state: State) -> dict:
    """驗證資料"""
    return {"validated": True}

def process_data(state: State) -> dict:
    """處理資料"""
    return {"processed": f"已處理: {state['data']}"}

# 建構 Graph
builder = StateGraph(State)
builder.add_node("fetch_data", fetch_data)
builder.add_node("validate_data", validate_data)
builder.add_node("process_data", process_data)

builder.add_edge(START, "fetch_data")
builder.add_edge("fetch_data", "validate_data")
builder.add_edge("validate_data", "process_data")
builder.add_edge("process_data", END)

checkpointer = MemorySaver()

# ============================================================
# interrupt_before: 在指定節點「之前」暫停
# interrupt_after: 在指定節點「之後」暫停
# ============================================================
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["process_data"],  # 在 process_data 之前暫停
)

config = {"configurable": {"thread_id": "static-bp-1"}}

# 第一次呼叫：執行 fetch_data -> validate_data -> [暫停]
print("=== 第一次呼叫 ===")
for chunk in graph.stream(
    {"data": "", "validated": False, "processed": ""},
    config=config,
    stream_mode="updates",
):
    print(f"更新: {chunk}")

state = graph.get_state(config)
print(f"\n暫停在: {state.next}")
# 暫停在: ('process_data',)
print(f"目前 State: validated={state.values['validated']}")
# 目前 State: validated=True

# ============================================================
# 恢復：用 Command(resume=None) 或直接傳 None
# 靜態 breakpoint 不需要傳 resume 值
# ============================================================
print("\n=== 恢復執行 ===")
for chunk in graph.stream(
    Command(resume=None),
    config=config,
    stream_mode="updates",
):
    print(f"更新: {chunk}")

# 更新: {'process_data': {'processed': '已處理: 從 API 取得的原始資料'}}
