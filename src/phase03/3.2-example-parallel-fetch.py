# 3.2 範例：平行資料擷取（Parallel Nodes）
# 展示一個節點連多條邊到不同目標，使目標節點在同一 super-step 中平行執行。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import operator
import time


# 1. 定義 State
# 使用 Annotated + operator.add 作為 reducer，讓多個平行節點的結果合併
class FetchState(TypedDict):
    query: str
    results: Annotated[list[str], operator.add]  # 平行節點的結果會合併
    timing: Annotated[list[str], operator.add]


# 2. 定義 Node 函數
def prepare(state: FetchState) -> dict:
    """準備階段"""
    print(f"[prepare] 收到查詢: '{state['query']}'")
    return {"timing": [f"prepare: 開始"]}


def fetch_database(state: FetchState) -> dict:
    """從資料庫擷取（模擬）"""
    time.sleep(0.1)  # 模擬延遲
    result = f"DB 結果：找到 '{state['query']}' 的 3 筆記錄"
    print(f"[fetch_database] {result}")
    return {"results": [result], "timing": ["fetch_database: 完成"]}


def fetch_api(state: FetchState) -> dict:
    """從外部 API 擷取（模擬）"""
    time.sleep(0.1)  # 模擬延遲
    result = f"API 結果：'{state['query']}' 的即時資料"
    print(f"[fetch_api] {result}")
    return {"results": [result], "timing": ["fetch_api: 完成"]}


def fetch_cache(state: FetchState) -> dict:
    """從快取擷取（模擬）"""
    result = f"快取結果：'{state['query']}' 的歷史資料"
    print(f"[fetch_cache] {result}")
    return {"results": [result], "timing": ["fetch_cache: 完成"]}


def combine(state: FetchState) -> dict:
    """合併所有來源的結果"""
    print(f"[combine] 合併 {len(state['results'])} 個結果")
    return {"timing": [f"combine: 合併了 {len(state['results'])} 個結果"]}


# 3. 建構 Graph（平行分支）
builder = StateGraph(FetchState)
builder.add_node("prepare", prepare)
builder.add_node("fetch_database", fetch_database)
builder.add_node("fetch_api", fetch_api)
builder.add_node("fetch_cache", fetch_cache)
builder.add_node("combine", combine)

# prepare 同時連接三個 fetch 節點 → 平行執行
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "fetch_database")
builder.add_edge("prepare", "fetch_api")
builder.add_edge("prepare", "fetch_cache")

# 三個 fetch 都連到 combine → 全部完成後才執行 combine
builder.add_edge("fetch_database", "combine")
builder.add_edge("fetch_api", "combine")
builder.add_edge("fetch_cache", "combine")

builder.add_edge("combine", END)

graph = builder.compile()

# 4. 執行
result = graph.invoke({
    "query": "LangGraph",
    "results": [],
    "timing": [],
})

print(f"\n=== 結果 ===")
for r in result["results"]:
    print(f"  - {r}")
print(f"\n執行順序:")
for t in result["timing"]:
    print(f"  - {t}")
