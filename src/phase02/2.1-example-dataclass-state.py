# 2.1 State Schema 設計 — 使用 Dataclass 定義 State 的完整範例
# 展示 Dataclass 的預設值便利性
# 不需要 API key

"""
使用 Dataclass 定義 State 的完整範例
展示預設值的便利性
"""
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State Schema（有預設值）
# ============================================================
@dataclass
class TaskState:
    task: str = ""                              # 任務描述
    steps: list[str] = field(default_factory=list)  # 已執行步驟
    status: str = "pending"                     # 狀態：pending/running/done
    error_count: int = 0                        # 錯誤計數

# ============================================================
# 2. 定義 Nodes
# ============================================================
def start_task(state: TaskState) -> dict:
    """開始任務"""
    return {
        "status": "running",
        "steps": ["started"],
    }

def execute_task(state: TaskState) -> dict:
    """執行任務"""
    new_steps = state.steps + [f"executed: {state.task}"]
    return {
        "steps": new_steps,
        "status": "done",
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(TaskState)
builder.add_node("start", start_task)
builder.add_node("execute", execute_task)
builder.add_edge(START, "start")
builder.add_edge("start", "execute")
builder.add_edge("execute", END)

graph = builder.compile()

# ============================================================
# 4. 執行——可以只傳部分欄位，其餘用預設值
# ============================================================
result = graph.invoke({"task": "生成報告"})
# 不需要傳 steps、status、error_count，它們有預設值

print(result)
# {
#     "task": "生成報告",
#     "steps": ["started", "executed: 生成報告"],
#     "status": "done",
#     "error_count": 0
# }
