# 16.2 範例：僅重試失敗分支
# 展示平行節點中部分失敗的恢復行為
# 需要：pip install langgraph

import uuid
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    results: Annotated[list[str], add]


branch_c_attempts = 0


def branch_a(state: State) -> dict:
    """分支 A：總是成功"""
    print("  [Branch A] 執行中...")
    return {"results": ["A: success"]}


def branch_b(state: State) -> dict:
    """分支 B：總是成功"""
    print("  [Branch B] 執行中...")
    return {"results": ["B: success"]}


def branch_c(state: State) -> dict:
    """分支 C：第一次失敗，第二次成功"""
    global branch_c_attempts
    branch_c_attempts += 1
    print(f"  [Branch C] 執行中... (attempt {branch_c_attempts})")

    if branch_c_attempts == 1:
        raise RuntimeError("Branch C 暫時失敗！")

    return {"results": ["C: success"]}


def merge(state: State) -> dict:
    """合併所有分支結果"""
    print(f"  [Merge] 結果: {state['results']}")
    return {"results": [f"merged: {len(state['results'])} branches"]}


# === 建構 Graph（平行分支） ===
builder = StateGraph(State)
builder.add_node("branch_a", branch_a)
builder.add_node("branch_b", branch_b)
builder.add_node("branch_c", branch_c)
builder.add_node("merge", merge)

# fan-out: START 到三個平行分支
builder.add_edge(START, "branch_a")
builder.add_edge(START, "branch_b")
builder.add_edge(START, "branch_c")

# fan-in: 三個分支匯聚到 merge
builder.add_edge("branch_a", "merge")
builder.add_edge("branch_b", "merge")
builder.add_edge("branch_c", "merge")
builder.add_edge("merge", END)

graph = builder.compile(checkpointer=InMemorySaver())

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# === 第一次執行：Branch C 會失敗 ===
print("=== 第一次執行 ===")
try:
    result = graph.invoke({"results": []}, config)
except RuntimeError as e:
    print(f"  失敗: {e}")

# === 恢復：只有 Branch C 會重新執行 ===
print("\n=== 恢復執行 ===")
result = graph.invoke(None, config)
print(f"\n最終結果: {result['results']}")

# 輸出：
# === 第一次執行 ===
#   [Branch A] 執行中...
#   [Branch B] 執行中...
#   [Branch C] 執行中... (attempt 1)
#   失敗: Branch C 暫時失敗！
#
# === 恢復執行 ===
#   [Branch C] 執行中... (attempt 2)    <- 只有 C 重新執行
#   [Merge] 結果: ['A: success', 'B: success', 'C: success']
