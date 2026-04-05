# 16.1 範例：故障恢復
# 展示如何在 node 失敗後從最近的 checkpoint 恢復
# 需要：pip install langgraph

import uuid
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

attempt_count = 0


class State(TypedDict):
    input: str
    step1_result: str
    step2_result: str


def step1(state: State) -> dict:
    """第一步：總是成功"""
    print("  執行 step1")
    return {"step1_result": f"step1 processed: {state['input']}"}


def step2(state: State) -> dict:
    """第二步：第一次會失敗，第二次成功"""
    global attempt_count
    attempt_count += 1
    print(f"  執行 step2 (attempt {attempt_count})")

    if attempt_count == 1:
        raise Exception("模擬 LLM API timeout！")

    return {"step2_result": f"step2 processed: {state['step1_result']}"}


# 建構 graph
builder = StateGraph(State)
builder.add_node("step1", step1)
builder.add_node("step2", step2)
builder.add_edge(START, "step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# === 第一次執行 — 會在 step2 失敗 ===
print("=== 第一次執行 ===")
try:
    result = graph.invoke({"input": "hello"}, config)
except Exception as e:
    print(f"  失敗: {e}")

# === 從失敗點恢復 ===
# 使用相同的 thread_id，傳入 None 作為 input
# LangGraph 會從 step2 開始（step1 的結果已保存）
print("\n=== 恢復執行 ===")
result = graph.invoke(None, config)  # None = 從 checkpoint 恢復
print(f"  結果: {result}")
# step1 不會重新執行！只有 step2 會重新執行
