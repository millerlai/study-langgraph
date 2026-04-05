# 10.1 範例：Supervisor 模式（中央協調者）
# Supervisor 根據任務類型分派給不同的 Worker Agent（研究、寫作、程式），
# 使用 LangGraph StateGraph 手動建構。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State
# ============================================================
class SupervisorState(TypedDict):
    task: str                               # 用戶任務
    task_type: str                          # 任務分類
    worker_output: str                      # Worker 輸出
    final_response: str                     # 最終回應
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. Supervisor 節點：分類任務
# ============================================================
def supervisor_classify(state: SupervisorState) -> dict:
    """Supervisor 分析任務並決定委派對象"""
    task = state["task"].lower()

    if any(kw in task for kw in ["查詢", "搜尋", "研究", "分析", "調查"]):
        task_type = "research"
    elif any(kw in task for kw in ["寫", "撰寫", "文章", "文案", "信件"]):
        task_type = "writing"
    elif any(kw in task for kw in ["程式", "程式碼", "函式", "api", "code"]):
        task_type = "coding"
    else:
        task_type = "research"  # 預設

    return {
        "task_type": task_type,
        "logs": [f"[Supervisor] 任務分類為: {task_type}"]
    }


# ============================================================
# 3. Worker Agent 節點
# ============================================================
def research_agent(state: SupervisorState) -> dict:
    """研究 Agent"""
    task = state["task"]
    return {
        "worker_output": f"[研究報告] 針對「{task}」的分析：\n"
                        f"  1. 市場趨勢：正向成長中\n"
                        f"  2. 競爭分析：3 家主要競爭者\n"
                        f"  3. 建議：建議深入研究用戶反饋",
        "logs": ["[研究 Agent] 完成研究報告"]
    }

def writing_agent(state: SupervisorState) -> dict:
    """寫作 Agent"""
    task = state["task"]
    return {
        "worker_output": f"[文案] 關於「{task}」：\n"
                        f"  標題：探索新視野\n"
                        f"  正文：在當今快速變化的環境中...\n"
                        f"  結論：期待與您共創未來。",
        "logs": ["[寫作 Agent] 完成文案撰寫"]
    }

def coding_agent(state: SupervisorState) -> dict:
    """程式 Agent"""
    task = state["task"]
    return {
        "worker_output": f"[程式碼] 針對「{task}」的實作：\n"
                        f"  ```python\n"
                        f"  def solution():\n"
                        f"      # 根據需求實作\n"
                        f"      return 'done'\n"
                        f"  ```",
        "logs": ["[程式 Agent] 完成程式碼生成"]
    }


# ============================================================
# 4. Supervisor 整合節點
# ============================================================
def supervisor_synthesize(state: SupervisorState) -> dict:
    """Supervisor 整合 Worker 的輸出"""
    worker_output = state.get("worker_output", "")
    task_type = state.get("task_type", "unknown")
    return {
        "final_response": f"=== Supervisor 回覆 ===\n"
                         f"任務類型: {task_type}\n"
                         f"處理結果:\n{worker_output}",
        "logs": ["[Supervisor] 整合完成，回覆用戶"]
    }


# ============================================================
# 5. 路由函式
# ============================================================
def route_to_worker(
    state: SupervisorState,
) -> Literal["research", "writing", "coding"]:
    """根據任務分類路由到對應的 Worker"""
    task_type = state.get("task_type", "research")
    return task_type


# ============================================================
# 6. 建立圖
# ============================================================
builder = StateGraph(SupervisorState)

# 加入節點
builder.add_node("classify", supervisor_classify)
builder.add_node("research", research_agent)
builder.add_node("writing", writing_agent)
builder.add_node("coding", coding_agent)
builder.add_node("synthesize", supervisor_synthesize)

# 設定邊
builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",
    route_to_worker,
    ["research", "writing", "coding"]
)
builder.add_edge("research", "synthesize")
builder.add_edge("writing", "synthesize")
builder.add_edge("coding", "synthesize")
builder.add_edge("synthesize", END)

supervisor_graph = builder.compile()


# ============================================================
# 7. 測試
# ============================================================
tasks = [
    "研究 LangGraph 的市場定位和競爭分析",
    "幫我撰寫一封給客戶的感謝信件",
    "寫一個 Python 函式來處理 API 回應",
]

for task in tasks:
    print(f"--- 任務: {task} ---")
    result = supervisor_graph.invoke({
        "task": task,
        "task_type": "",
        "worker_output": "",
        "final_response": "",
        "logs": []
    })
    for log in result["logs"]:
        print(f"  {log}")
    print(f"{result['final_response']}\n")
