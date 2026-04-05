# 5.2 範例：子圖中的中斷處理
# 展示中斷從子圖冒泡到父圖，以及 Command(resume=...) 自動路由到子圖
"""
子圖中的中斷處理：中斷從子圖冒泡到父圖
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

# ============================================================
# 1. 定義子圖 (Subgraph)
# ============================================================
class SubState(TypedDict):
    sub_task: str
    sub_result: str

def sub_analyze(state: SubState) -> dict:
    """子圖：分析步驟"""
    return {"sub_result": f"分析結果：{state['sub_task']}"}

def sub_confirm(state: SubState) -> dict:
    """子圖：確認步驟——會中斷！"""
    confirmation = interrupt({
        "source": "subgraph",
        "message": f"子圖需要確認：{state['sub_result']}",
    })
    return {"sub_result": f"{state['sub_result']} [已確認: {confirmation}]"}

sub_builder = StateGraph(SubState)
sub_builder.add_node("sub_analyze", sub_analyze)
sub_builder.add_node("sub_confirm", sub_confirm)
sub_builder.add_edge(START, "sub_analyze")
sub_builder.add_edge("sub_analyze", "sub_confirm")
sub_builder.add_edge("sub_confirm", END)

# 子圖不需要自己的 checkpointer——它會繼承父圖的
subgraph = sub_builder.compile()

# ============================================================
# 2. 定義父圖 (Parent Graph)
# ============================================================
class ParentState(TypedDict):
    task: str
    sub_task: str
    sub_result: str
    final_result: str

def prepare(state: ParentState) -> dict:
    """父圖：準備工作"""
    return {"sub_task": f"子任務（來自：{state['task']}）"}

def finalize(state: ParentState) -> dict:
    """父圖：最終化"""
    return {"final_result": f"完成！子圖結果: {state['sub_result']}"}

parent_builder = StateGraph(ParentState)
parent_builder.add_node("prepare", prepare)
parent_builder.add_node("subgraph", subgraph)  # 嵌入子圖作為節點
parent_builder.add_node("finalize", finalize)

parent_builder.add_edge(START, "prepare")
parent_builder.add_edge("prepare", "subgraph")
parent_builder.add_edge("subgraph", "finalize")
parent_builder.add_edge("finalize", END)

# 父圖配置 checkpointer
checkpointer = MemorySaver()
parent_graph = parent_builder.compile(checkpointer=checkpointer)

# ============================================================
# 3. 執行
# ============================================================
config = {"configurable": {"thread_id": "subgraph-interrupt-1"}}

print("=== 第一次呼叫（子圖中會中斷）===")
for chunk in parent_graph.stream(
    {"task": "資料分析", "sub_task": "", "sub_result": "", "final_result": ""},
    config=config,
    stream_mode="values",
):
    print(f"  State: task={chunk.get('task', '')}, sub_result={chunk.get('sub_result', '')}")

state = parent_graph.get_state(config)
print(f"\n暫停在: {state.next}")
# 暫停在: ('subgraph',)
# （中斷從子圖的 sub_confirm 冒泡到父圖的 subgraph 節點）

# ============================================================
# 4. 恢復——Command(resume=...) 自動傳到子圖
# ============================================================
print("\n=== 恢復執行 ===")
for chunk in parent_graph.stream(
    Command(resume="approved"),
    config=config,
    stream_mode="values",
):
    print(f"  State: sub_result={chunk.get('sub_result', '')}, final={chunk.get('final_result', '')}")

result = parent_graph.get_state(config)
print(f"\n最終結果: {result.values['final_result']}")
# 最終結果: 完成！子圖結果: 分析結果：子任務（來自：資料分析） [已確認: approved]
