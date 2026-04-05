# 3.1 範例：迴圈（Loops）
# 展示透過條件邊讓節點回到自己，實現數字迭代收斂的迴圈模式。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義 State
class IterState(TypedDict):
    value: float
    target: float
    iterations: int
    history: list[float]


# 2. 定義 Node 函數
def process(state: IterState) -> dict:
    """每次迭代：將 value 往 target 靠近一半"""
    current = state["value"]
    target = state["target"]
    new_value = current + (target - current) * 0.5
    iterations = state["iterations"] + 1
    history = state.get("history", []) + [new_value]
    print(f"[process] 迭代 {iterations}: {current:.4f} -> {new_value:.4f} (目標: {target})")
    return {
        "value": new_value,
        "iterations": iterations,
        "history": history,
    }


# 3. 定義路由函數（決定繼續或結束）
def should_continue(state: IterState) -> str:
    """檢查是否足夠接近目標"""
    diff = abs(state["value"] - state["target"])
    if diff < 0.01 or state["iterations"] >= 20:
        print(f"[should_continue] 結束！差距={diff:.4f}, 迭代={state['iterations']}")
        return "done"
    return "continue"


# 4. 建構 Graph（迴圈結構）
builder = StateGraph(IterState)
builder.add_node("process", process)

builder.add_edge(START, "process")

# 條件邊形成迴圈：process → 檢查 → 回到 process 或結束
builder.add_conditional_edges(
    "process",
    should_continue,
    {
        "continue": "process",  # 迴圈：回到自己
        "done": END,            # 結束
    }
)

graph = builder.compile()

# 5. 執行
result = graph.invoke({
    "value": 0.0,
    "target": 100.0,
    "iterations": 0,
    "history": [],
})

print(f"\n最終值: {result['value']:.4f}")
print(f"總迭代: {result['iterations']}")
print(f"歷史: {[f'{v:.2f}' for v in result['history']]}")
