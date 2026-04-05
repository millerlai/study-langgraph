# 3.2 範例：Map-Reduce 與 Send API
# 展示使用 Send API 實現動態平行的 Map-Reduce 模式——平行文章產生器。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator


# 1. 定義 State
class OverallState(TypedDict):
    topics: list[str]
    articles: Annotated[list[str], operator.add]
    final_report: str


# Worker 節點接收的 State（與主 State 不同）
class WorkerState(TypedDict):
    topic: str


# 2. 定義 Node 函數
def planner(state: OverallState) -> dict:
    """規劃階段：決定要處理哪些主題"""
    topics = state["topics"]
    print(f"[planner] 規劃 {len(topics)} 個主題: {topics}")
    return {}  # topics 已在輸入中，不需更新


def generate_article(state: WorkerState) -> dict:
    """Worker：為單一主題產生文章（Map 階段）"""
    topic = state["topic"]
    article = f"【{topic}】這是關於 {topic} 的深度分析文章，探討了核心概念與實際應用。"
    print(f"[generate_article] 產生文章: {topic}")
    return {"articles": [article]}


def collect_results(state: OverallState) -> dict:
    """收集階段：合併所有文章（Reduce 階段）"""
    articles = state["articles"]
    report = f"報告摘要：共 {len(articles)} 篇文章\n"
    for i, article in enumerate(articles, 1):
        report += f"  {i}. {article[:30]}...\n"
    print(f"[collect_results] 合併 {len(articles)} 篇文章")
    return {"final_report": report}


# 3. 定義 Send 路由函數
def distribute_to_workers(state: OverallState):
    """動態產生 Send 物件，每個主題一個 worker"""
    return [
        Send("generate_article", {"topic": topic})
        for topic in state["topics"]
    ]


# 4. 建構 Graph
builder = StateGraph(OverallState)
builder.add_node("planner", planner)
builder.add_node("generate_article", generate_article)
builder.add_node("collect_results", collect_results)

builder.add_edge(START, "planner")

# 使用條件邊 + Send 實現動態平行
builder.add_conditional_edges("planner", distribute_to_workers, ["generate_article"])

builder.add_edge("generate_article", "collect_results")
builder.add_edge("collect_results", END)

graph = builder.compile()

# 5. 執行
result = graph.invoke({
    "topics": ["LangGraph 基礎", "State 管理", "控制流設計", "多 Agent 架構"],
    "articles": [],
    "final_report": "",
})

print(f"\n=== 最終報告 ===")
print(result["final_report"])
print(f"文章數量: {len(result['articles'])}")
