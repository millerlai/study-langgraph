# 9.1 範例：Checkpoint Namespace
# 展示父圖和子圖各自擁有獨立的 checkpoint 命名空間，
# checkpointer 只需要在父圖層級設定即可自動傳播到子圖。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義共享 State
# ============================================================
class WorkflowState(TypedDict):
    task: str
    steps: Annotated[list[str], lambda x, y: x + y]
    result: str


# ============================================================
# 2. 定義子圖
# ============================================================
def sub_step_1(state: WorkflowState) -> dict:
    return {"steps": ["[子圖] 步驟 1: 資料收集"]}

def sub_step_2(state: WorkflowState) -> dict:
    return {"steps": ["[子圖] 步驟 2: 資料處理"]}

sub_builder = StateGraph(WorkflowState)
sub_builder.add_node("step1", sub_step_1)
sub_builder.add_node("step2", sub_step_2)
sub_builder.add_edge(START, "step1")
sub_builder.add_edge("step1", "step2")
sub_builder.add_edge("step2", END)
sub_graph = sub_builder.compile()
# 注意：子圖不需要單獨設定 checkpointer


# ============================================================
# 3. 定義父圖
# ============================================================
def init_task(state: WorkflowState) -> dict:
    return {"steps": [f"[父圖] 初始化任務: {state['task']}"]}

def finalize(state: WorkflowState) -> dict:
    return {
        "result": f"完成！共執行 {len(state['steps'])} 個步驟",
        "steps": ["[父圖] 完成"]
    }

parent_builder = StateGraph(WorkflowState)
parent_builder.add_node("init", init_task)
parent_builder.add_node("process", sub_graph)       # 子圖作為節點
parent_builder.add_node("finalize", finalize)

parent_builder.add_edge(START, "init")
parent_builder.add_edge("init", "process")
parent_builder.add_edge("process", "finalize")
parent_builder.add_edge("finalize", END)

# 只在父圖層級設定 checkpointer —— 會自動傳播到子圖
checkpointer = InMemorySaver()
parent_graph = parent_builder.compile(checkpointer=checkpointer)


# ============================================================
# 4. 執行並檢視 Checkpoint
# ============================================================
config = {"configurable": {"thread_id": "demo-thread-1"}}

# 執行圖
result = parent_graph.invoke(
    {"task": "分析用戶反饋", "steps": [], "result": ""},
    config=config
)

print("=== 執行結果 ===")
print(f"結果: {result['result']}")
print(f"步驟:")
for step in result["steps"]:
    print(f"  {step}")

# 檢視 checkpoint 歷史
print("\n=== Checkpoint 歷史 ===")
for state_snapshot in parent_graph.get_state_history(config):
    node = state_snapshot.metadata.get("source", "unknown")
    step_count = len(state_snapshot.values.get("steps", []))
    ns = state_snapshot.config["configurable"].get("checkpoint_ns", "(root)")
    print(f"  Node: {node:12s} | Steps: {step_count} | Namespace: {ns}")
