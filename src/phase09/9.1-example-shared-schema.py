# 9.1 範例：父子圖共享 State Schema
# 展示子圖負責「研究分析」，父圖負責整體流程控制，兩者共享同一個 State Schema。
# 子圖直接作為節點加入父圖。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義共享的 State Schema
# ============================================================
class SharedState(TypedDict):
    topic: str                              # 研究主題
    research_notes: Annotated[list[str], lambda x, y: x + y]  # 研究筆記（累加）
    summary: str                            # 最終摘要


# ============================================================
# 2. 定義子圖：研究分析模組
# ============================================================
def gather_info(state: SharedState) -> dict:
    """收集資訊節點"""
    topic = state["topic"]
    return {
        "research_notes": [f"[收集] 已蒐集關於 '{topic}' 的基礎資料"]
    }

def analyze_info(state: SharedState) -> dict:
    """分析資訊節點"""
    notes_count = len(state.get("research_notes", []))
    return {
        "research_notes": [f"[分析] 已分析 {notes_count} 條筆記，發現 3 個關鍵觀點"]
    }

# 建立子圖
research_builder = StateGraph(SharedState)
research_builder.add_node("gather", gather_info)
research_builder.add_node("analyze", analyze_info)
research_builder.add_edge(START, "gather")
research_builder.add_edge("gather", "analyze")
research_builder.add_edge("analyze", END)

# 編譯子圖
research_subgraph = research_builder.compile()


# ============================================================
# 3. 定義父圖
# ============================================================
def plan_research(state: SharedState) -> dict:
    """規劃研究方向"""
    return {
        "research_notes": [f"[規劃] 確定研究主題：{state['topic']}"]
    }

def write_summary(state: SharedState) -> dict:
    """撰寫摘要"""
    all_notes = state.get("research_notes", [])
    summary_text = f"研究摘要：共有 {len(all_notes)} 條筆記\n"
    for note in all_notes:
        summary_text += f"  - {note}\n"
    return {"summary": summary_text}


# 建立父圖，直接將子圖作為節點
parent_builder = StateGraph(SharedState)
parent_builder.add_node("plan", plan_research)
parent_builder.add_node("research", research_subgraph)   # <-- 直接加入子圖
parent_builder.add_node("summarize", write_summary)

parent_builder.add_edge(START, "plan")
parent_builder.add_edge("plan", "research")
parent_builder.add_edge("research", "summarize")
parent_builder.add_edge("summarize", END)

parent_graph = parent_builder.compile()


# ============================================================
# 4. 執行
# ============================================================
result = parent_graph.invoke({
    "topic": "LangGraph 子圖設計模式",
    "research_notes": [],
    "summary": ""
})

print("=== 研究筆記 ===")
for note in result["research_notes"]:
    print(f"  {note}")
print(f"\n=== 摘要 ===\n{result['summary']}")
