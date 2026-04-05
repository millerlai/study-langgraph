# 9.2 範例：子圖間透過父圖 State 間接傳遞資料
# 子圖 A（資料收集）寫入 collected_data，子圖 B（資料分析）讀取並分析。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 共享 State
# ============================================================
class PipelineState(TypedDict):
    input_query: str
    collected_data: list[str]          # 子圖 A 寫入，子圖 B 讀取
    analysis_result: str               # 子圖 B 寫入
    logs: Annotated[list[str], lambda x, y: x + y]


# ============================================================
# 2. 子圖 A：資料收集
# ============================================================
def collect_from_source_1(state: PipelineState) -> dict:
    query = state.get("input_query", "")
    return {
        "collected_data": [f"來源1的資料: {query}相關結果"],
        "logs": ["[收集器] 從來源 1 取得資料"]
    }

def collect_from_source_2(state: PipelineState) -> dict:
    existing = state.get("collected_data", [])
    return {
        "collected_data": existing + ["來源2的資料: 補充資訊"],
        "logs": ["[收集器] 從來源 2 取得資料"]
    }

collector_builder = StateGraph(PipelineState)
collector_builder.add_node("source1", collect_from_source_1)
collector_builder.add_node("source2", collect_from_source_2)
collector_builder.add_edge(START, "source1")
collector_builder.add_edge("source1", "source2")
collector_builder.add_edge("source2", END)
collector_subgraph = collector_builder.compile()


# ============================================================
# 3. 子圖 B：資料分析
# ============================================================
def analyze_data(state: PipelineState) -> dict:
    data = state.get("collected_data", [])
    # 子圖 B 讀取子圖 A 寫入的 collected_data
    analysis = f"分析了 {len(data)} 筆資料，發現關鍵模式"
    return {
        "analysis_result": analysis,
        "logs": [f"[分析器] {analysis}"]
    }

def generate_insights(state: PipelineState) -> dict:
    return {
        "analysis_result": f"{state['analysis_result']} -> 產生 3 個洞察",
        "logs": ["[分析器] 洞察生成完成"]
    }

analyzer_builder = StateGraph(PipelineState)
analyzer_builder.add_node("analyze", analyze_data)
analyzer_builder.add_node("insights", generate_insights)
analyzer_builder.add_edge(START, "analyze")
analyzer_builder.add_edge("analyze", "insights")
analyzer_builder.add_edge("insights", END)
analyzer_subgraph = analyzer_builder.compile()


# ============================================================
# 4. 父圖：管線
# ============================================================
parent_builder = StateGraph(PipelineState)
parent_builder.add_node("collect", collector_subgraph)    # 子圖 A
parent_builder.add_node("analyze", analyzer_subgraph)     # 子圖 B
parent_builder.add_edge(START, "collect")
parent_builder.add_edge("collect", "analyze")             # A 完成後自動到 B
parent_builder.add_edge("analyze", END)

pipeline = parent_builder.compile()


# ============================================================
# 5. 執行
# ============================================================
result = pipeline.invoke({
    "input_query": "LangGraph 最佳實踐",
    "collected_data": [],
    "analysis_result": "",
    "logs": []
})

print("=== 處理日誌 ===")
for log in result["logs"]:
    print(f"  {log}")
print(f"\n收集的資料: {result['collected_data']}")
print(f"分析結果: {result['analysis_result']}")
