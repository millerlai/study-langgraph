# 5.2 範例：檢視並修改 Agent State
# 展示人類在中斷期間審核計畫，用 Command(resume=...) 接受或修改後繼續
"""
檢視並修改 Agent State：人類在中斷期間修改 State，然後繼續
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import operator

class State(TypedDict):
    query: str
    plan: list[str]
    results: Annotated[list[str], operator.add]
    final_answer: str

def create_plan(state: State) -> dict:
    """Agent 建立執行計畫"""
    query = state["query"]
    plan = [
        f"步驟1: 搜尋「{query}」的相關資料",
        f"步驟2: 分析搜尋結果",
        f"步驟3: 生成摘要",
    ]
    return {"plan": plan}

def review_plan(state: State) -> dict:
    """讓人類審核計畫"""
    feedback = interrupt({
        "message": "請審核以下執行計畫",
        "plan": state["plan"],
        "instruction": "回覆 'ok' 接受，或提供修改後的計畫 list",
    })

    if feedback == "ok":
        return {"results": ["計畫已通過人類審核"]}
    elif isinstance(feedback, list):
        # 人類提供了修改後的計畫
        return {"plan": feedback, "results": ["計畫已被人類修改"]}
    else:
        return {"results": [f"人類回饋: {feedback}"]}

def execute_plan(state: State) -> dict:
    """執行計畫"""
    executed = []
    for step in state["plan"]:
        executed.append(f"完成 - {step}")
    return {"results": executed}

def summarize(state: State) -> dict:
    """生成最終答案"""
    all_results = "\n".join(state["results"])
    return {"final_answer": f"最終答案（基於 {len(state['plan'])} 個步驟的執行結果）"}

# 建構 Graph
builder = StateGraph(State)
builder.add_node("create_plan", create_plan)
builder.add_node("review_plan", review_plan)
builder.add_node("execute_plan", execute_plan)
builder.add_node("summarize", summarize)

builder.add_edge(START, "create_plan")
builder.add_edge("create_plan", "review_plan")
builder.add_edge("review_plan", "execute_plan")
builder.add_edge("execute_plan", "summarize")
builder.add_edge("summarize", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "review-state-1"}}

# ============================================================
# 第一次呼叫：建立計畫後暫停
# ============================================================
graph.invoke(
    {"query": "LangGraph 最佳實踐", "plan": [], "results": [], "final_answer": ""},
    config=config,
)

# ============================================================
# 檢查目前的 State
# ============================================================
current_state = graph.get_state(config)
print("=== 目前 State ===")
print(f"query: {current_state.values['query']}")
print(f"plan: {current_state.values['plan']}")
print(f"next: {current_state.next}")

# === 目前 State ===
# query: LangGraph 最佳實踐
# plan: ['步驟1: 搜尋「LangGraph 最佳實踐」的相關資料', '步驟2: 分析搜尋結果', '步驟3: 生成摘要']
# next: ('review_plan',)

# ============================================================
# 方法 A：直接用 Command(resume=...) 回覆
# ============================================================
result = graph.invoke(Command(resume="ok"), config=config)
print(f"\n最終答案: {result['final_answer']}")
# 最終答案: 最終答案（基於 3 個步驟的執行結果）
