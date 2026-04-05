# 10.1 範例：Hierarchical Agent 團隊（階層式）
# 頂層 Supervisor 管理兩個子團隊：
# - 研究團隊（Research Supervisor + Web 搜尋 + 資料分析）
# - 內容團隊（Content Supervisor + 寫作 + 編輯）

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State
# ============================================================
class HierarchicalState(TypedDict):
    task: str
    research_output: str
    content_output: str
    final_output: str
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. 研究團隊（子圖）
# ============================================================
def web_search(state: HierarchicalState) -> dict:
    return {
        "research_output": f"[Web搜尋] 找到關於 '{state['task']}' 的 5 篇文章",
        "logs": ["  [Web搜尋] 搜尋完成"]
    }

def data_analysis(state: HierarchicalState) -> dict:
    existing = state.get("research_output", "")
    return {
        "research_output": f"{existing}\n[資料分析] 統計分析完成，發現 3 個趨勢",
        "logs": ["  [資料分析] 分析完成"]
    }

def research_supervisor(state: HierarchicalState) -> dict:
    return {"logs": ["[Research Supervisor] 研究團隊任務完成，整合結果"]}

research_builder = StateGraph(HierarchicalState)
research_builder.add_node("web_search", web_search)
research_builder.add_node("data_analysis", data_analysis)
research_builder.add_node("research_sup", research_supervisor)
research_builder.add_edge(START, "web_search")
research_builder.add_edge("web_search", "data_analysis")
research_builder.add_edge("data_analysis", "research_sup")
research_builder.add_edge("research_sup", END)
research_team = research_builder.compile()


# ============================================================
# 3. 內容團隊（子圖）
# ============================================================
def writer(state: HierarchicalState) -> dict:
    research = state.get("research_output", "無研究資料")
    return {
        "content_output": f"[寫作] 基於研究結果撰寫文章草稿\n  參考: {research[:60]}...",
        "logs": ["  [寫作Agent] 草稿撰寫完成"]
    }

def editor(state: HierarchicalState) -> dict:
    content = state.get("content_output", "")
    return {
        "content_output": f"{content}\n[編輯] 已校對和優化，文章品質: 優",
        "logs": ["  [編輯Agent] 編輯校對完成"]
    }

def content_supervisor(state: HierarchicalState) -> dict:
    return {"logs": ["[Content Supervisor] 內容團隊任務完成"]}

content_builder = StateGraph(HierarchicalState)
content_builder.add_node("writer", writer)
content_builder.add_node("editor", editor)
content_builder.add_node("content_sup", content_supervisor)
content_builder.add_edge(START, "writer")
content_builder.add_edge("writer", "editor")
content_builder.add_edge("editor", "content_sup")
content_builder.add_edge("content_sup", END)
content_team = content_builder.compile()


# ============================================================
# 4. 頂層 Supervisor
# ============================================================
def top_supervisor_plan(state: HierarchicalState) -> dict:
    return {"logs": ["[Top Supervisor] 制定計畫：先研究 -> 再產出內容"]}

def top_supervisor_finalize(state: HierarchicalState) -> dict:
    research = state.get("research_output", "無")
    content = state.get("content_output", "無")
    return {
        "final_output": (
            f"=== 最終產出 ===\n"
            f"任務: {state['task']}\n\n"
            f"研究成果:\n{research}\n\n"
            f"內容產出:\n{content}"
        ),
        "logs": ["[Top Supervisor] 所有團隊完成，最終產出已整合"]
    }


# ============================================================
# 5. 建立頂層圖
# ============================================================
top_builder = StateGraph(HierarchicalState)
top_builder.add_node("plan", top_supervisor_plan)
top_builder.add_node("research_team", research_team)    # 研究團隊子圖
top_builder.add_node("content_team", content_team)      # 內容團隊子圖
top_builder.add_node("finalize", top_supervisor_finalize)

top_builder.add_edge(START, "plan")
top_builder.add_edge("plan", "research_team")
top_builder.add_edge("research_team", "content_team")
top_builder.add_edge("content_team", "finalize")
top_builder.add_edge("finalize", END)

hierarchical_graph = top_builder.compile()


# ============================================================
# 6. 執行
# ============================================================
result = hierarchical_graph.invoke({
    "task": "撰寫一篇關於 AI Agent 趨勢的深度分析報告",
    "research_output": "",
    "content_output": "",
    "final_output": "",
    "logs": []
})

print("=== 執行日誌 ===")
for log in result["logs"]:
    print(f"  {log}")
print(f"\n{result['final_output']}")
