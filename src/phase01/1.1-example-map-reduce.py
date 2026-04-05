# 1.1 LangGraph 概觀 — 動態平行處理（Map-Reduce）範例
# 展示使用 Send 動態建立平行分支，處理不定數量的項目
# 不需要 API key

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator

# 1. 定義 State
class OverallState(TypedDict):
    """主 Graph 的 State"""
    articles: list[str]                                     # 輸入：多篇文章
    summaries: Annotated[list[str], operator.add]           # 各篇摘要（reducer 累加）
    final_report: str                                       # 最終彙整報告

class ArticleState(TypedDict):
    """單篇文章處理用的 State（每個平行分支獨立）"""
    article: str                                            # 單篇文章內容

# 2. 收集節點——動態 fan-out，為每篇文章建立一個平行分支
def collect_articles(state: OverallState):
    """用 Send 為每篇文章動態派發一個 summarize 節點"""
    return [
        Send("summarize", {"article": article})
        for article in state["articles"]
    ]

# 3. 摘要節點——每個平行分支獨立執行
def summarize(state: ArticleState) -> dict:
    """摘要單篇文章（實際應用會呼叫 LLM）"""
    article = state["article"]
    summary = f"摘要：{article[:20]}..."  # 模擬 LLM 摘要
    # 回傳到主 State 的 summaries 欄位（透過 reducer 累加）
    return {"summaries": [summary]}

# 4. 彙整節點——所有平行分支完成後執行
def aggregate(state: OverallState) -> dict:
    """將所有摘要彙整成最終報告"""
    all_summaries = "\n".join(
        f"  {i+1}. {s}" for i, s in enumerate(state["summaries"])
    )
    report = f"總結報告（共 {len(state['summaries'])} 篇）:\n{all_summaries}"
    return {"final_report": report}

# 5. 建構 Graph
builder = StateGraph(OverallState)

builder.add_node("summarize", summarize)
builder.add_node("aggregate", aggregate)

# START → 動態 fan-out（用 conditional_edges + Send）
builder.add_conditional_edges(START, collect_articles, ["summarize"])

# 所有 summarize 分支完成後 → aggregate
builder.add_edge("summarize", "aggregate")

# aggregate → END
builder.add_edge("aggregate", END)

graph = builder.compile()

# 6. 執行
result = graph.invoke({
    "articles": [
        "LangGraph 是一個低階的 AI agent 編排框架，專門用來建構 stateful agent...",
        "LangChain 提供高階元件，包括 model wrapper、prompt template、retriever...",
        "LangSmith 是一個可觀測性平台，提供 tracing、evaluation、除錯功能...",
    ],
    "summaries": [],
    "final_report": "",
})

print(result["final_report"])
# 總結報告（共 3 篇）:
#   1. 摘要：LangGraph 是一個低階的 AI...
#   2. 摘要：LangChain 提供高階元件，包括...
#   3. 摘要：LangSmith 是一個可觀測性平台...
