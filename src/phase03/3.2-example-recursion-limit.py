# 3.2 範例：遞迴限制（Recursion Limit）
# 展示設定與處理遞迴限制，以及使用 RemainingSteps 主動監控剩餘步數。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError


# 1. 定義 State
class CounterState(TypedDict):
    count: int
    max_count: int


# 2. 定義 Node
def increment(state: CounterState) -> dict:
    new_count = state["count"] + 1
    return {"count": new_count}


def check_done(state: CounterState) -> str:
    if state["count"] >= state["max_count"]:
        return "done"
    return "continue"


# 3. 建構有迴圈的 Graph
builder = StateGraph(CounterState)
builder.add_node("increment", increment)

builder.add_edge(START, "increment")
builder.add_conditional_edges(
    "increment",
    check_done,
    {"continue": "increment", "done": END}
)

graph = builder.compile()


# === 範例 1：正常執行（在限制內）===
print("=== 範例 1：正常執行 ===")
result = graph.invoke(
    {"count": 0, "max_count": 5},
    config={"recursion_limit": 10}
)
print(f"最終 count: {result['count']}")
# 最終 count: 5


# === 範例 2：觸發遞迴限制 ===
print("\n=== 範例 2：觸發遞迴限制 ===")
try:
    result = graph.invoke(
        {"count": 0, "max_count": 100},
        config={"recursion_limit": 5}  # 故意設很低
    )
except GraphRecursionError as e:
    print(f"捕捉到 GraphRecursionError: {e}")
    print("提示：增加 recursion_limit 或檢查迴圈邏輯")
