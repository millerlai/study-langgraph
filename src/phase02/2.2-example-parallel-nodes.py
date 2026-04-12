# 2.2 Reducer 機制 — 平行節點與 Reducer 的互動
# 展示多個節點同時更新同一欄位時 Reducer 的行為
# 不需要 API key

"""
平行節點與 Reducer 的互動
展示多個節點同時更新同一欄位時 Reducer 的行為
"""
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State
# ============================================================
class State(TypedDict):
    results: Annotated[list[str], add]    # 有 Reducer → 合併
    status: str                           # 無 Reducer → 覆蓋

# ============================================================
# 2. 定義平行節點
# ============================================================
def research(state: State) -> dict:
    """研究節點"""
    return {
        "results": ["[Research] 找到 3 篇相關論文"],
        # ⚠️ 不可在此更新 status！
        # 平行節點同時更新無 Reducer 的欄位 → InvalidUpdateError
    }

def analyze(state: State) -> dict:
    """分析節點"""
    return {
        "results": ["[Analyze] 完成數據分析"],
        # ⚠️ 同理，不可在此更新 status
    }

def summarize(state: State) -> dict:
    """彙總節點（非平行，可安全更新 status）"""
    return {
        "results": ["[Summary] " + " | ".join(state["results"])],
        "status": "done",
    }

# ============================================================
# 3. 建構 Graph（research 和 analyze 平行執行）
# ============================================================
builder = StateGraph(State)
builder.add_node("research", research)
builder.add_node("analyze", analyze)
builder.add_node("summarize", summarize)

# START → research 和 analyze（平行）
builder.add_edge(START, "research")
builder.add_edge(START, "analyze")

# 兩者都完成後 → summarize
builder.add_edge("research", "summarize")
builder.add_edge("analyze", "summarize")

builder.add_edge("summarize", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({"results": [], "status": "init"})
print("Results:", result["results"])
# Results: [
#     "[Research] 找到 3 篇相關論文",
#     "[Analyze] 完成數據分析",
#     "[Summary] [Research] 找到 3 篇相關論文 | [Analyze] 完成數據分析"
# ]
# → results 欄位透過 Reducer 正確合併了兩個平行節點的輸出

print("Status:", result["status"])
# Status: done
# → status 欄位沒有 Reducer，只能在非平行的 summarize 節點更新
# → 若平行節點同時更新無 Reducer 的欄位，LangGraph 會拋出 InvalidUpdateError
