# 10.2 範例：分治法 (Divide-and-Conquer)
# Planner 將複雜問題拆分為多個子任務，每個子任務由 Worker 處理（使用 Send 平行分發），
# 最後由 Aggregator 合併所有結果。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# ============================================================
# 1. 定義 State
# ============================================================
class DnCState(TypedDict):
    complex_task: str                       # 複雜任務描述
    subtasks: list[str]                     # 拆分後的子任務
    subtask_results: Annotated[list[str], lambda x, y: x + y]
    final_result: str
    logs: Annotated[list[str], lambda x, y: x + y]


class SubtaskState(TypedDict):
    """單一子任務的 State"""
    subtask: str
    subtask_results: Annotated[list[str], lambda x, y: x + y]
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. Planner：拆分任務
# ============================================================
def planner(state: DnCState) -> dict:
    """將複雜任務拆分為多個子任務"""
    task = state["complex_task"]

    # 模擬任務拆分邏輯
    subtasks = [
        f"子任務1: 針對「{task}」進行背景研究",
        f"子任務2: 針對「{task}」收集數據",
        f"子任務3: 針對「{task}」撰寫分析報告",
    ]

    return {
        "subtasks": subtasks,
        "logs": [f"[Planner] 已將任務拆分為 {len(subtasks)} 個子任務"]
    }


# ============================================================
# 3. Worker：處理子任務
# ============================================================
def worker(state: SubtaskState) -> dict:
    """處理單一子任務"""
    subtask = state["subtask"]
    result = f"[完成] {subtask} -> 發現 2 個關鍵洞察"
    return {
        "subtask_results": [result],
        "logs": [f"[Worker] 完成: {subtask[:30]}..."]
    }


# ============================================================
# 4. Fan-out 邏輯：平行分發子任務
# ============================================================
def distribute_subtasks(state: DnCState) -> list[Send]:
    """將子任務 fan-out 到多個 Worker"""
    sends = []
    for subtask in state.get("subtasks", []):
        sends.append(Send("worker", {
            "subtask": subtask,
            "subtask_results": [],
            "logs": []
        }))
    return sends


# ============================================================
# 5. Aggregator：合併結果
# ============================================================
def aggregator(state: DnCState) -> dict:
    """合併所有子任務的結果"""
    results = state.get("subtask_results", [])
    merged = f"=== 分治法結果 ===\n"
    merged += f"原始任務: {state['complex_task']}\n"
    merged += f"子任務數: {len(results)}\n\n"
    for i, result in enumerate(results, 1):
        merged += f"  {i}. {result}\n"
    merged += f"\n綜合結論: 基於 {len(results)} 個子任務的分析，任務已完成。"

    return {
        "final_result": merged,
        "logs": [f"[Aggregator] 已合併 {len(results)} 個子任務結果"]
    }


# ============================================================
# 6. 建立圖
# ============================================================
builder = StateGraph(DnCState)

builder.add_node("planner", planner)
builder.add_node("worker", worker)
builder.add_node("aggregator", aggregator)

builder.add_edge(START, "planner")
builder.add_conditional_edges("planner", distribute_subtasks, ["worker"])
builder.add_edge("worker", "aggregator")
builder.add_edge("aggregator", END)

dnc_graph = builder.compile()


# ============================================================
# 7. 執行
# ============================================================
result = dnc_graph.invoke({
    "complex_task": "評估 AI Agent 在企業中的應用前景",
    "subtasks": [],
    "subtask_results": [],
    "final_result": "",
    "logs": []
})

print("=== 執行日誌 ===")
for log in result["logs"]:
    print(f"  {log}")
print(f"\n{result['final_result']}")
