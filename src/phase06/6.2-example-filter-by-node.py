# 6.2 範例：依節點過濾串流輸出
# 展示在 updates 模式下只接收特定節點的 state 更新
"""
依節點過濾串流輸出
只接收特定節點的 state 更新
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    query: str
    search_result: str
    analysis: str
    response: str


def search_node(state: State) -> dict:
    return {"search_result": f"搜尋「{state['query']}」的結果：LangGraph 是圖狀態機框架"}


def analyze_node(state: State) -> dict:
    return {"analysis": f"分析結果：{state['search_result']} => 這是一個重要的 AI 工具"}


def respond_node(state: State) -> dict:
    return {"response": f"回答：根據分析，{state['analysis']}"}


graph = (
    StateGraph(State)
    .add_node("search", search_node)
    .add_node("analyze", analyze_node)
    .add_node("respond", respond_node)
    .add_edge(START, "search")
    .add_edge("search", "analyze")
    .add_edge("analyze", "respond")
    .add_edge("respond", END)
    .compile()
)

# 使用 updates 模式，只過濾 respond 節點的��出
print("=== 只顯示 respond 節點的輸出 ===")
for chunk in graph.stream(
    {"query": "什麼是 LangGraph？"},
    stream_mode="updates",
    version="v2",
):
    # chunk["data"] 是 {node_name: state_update} 的 dict
    if "respond" in chunk["data"]:
        print(f"回應節點輸出: {chunk['data']['respond']}")

print()
print("=== 顯示所有節點（對比） ===")
for chunk in graph.stream(
    {"query": "什麼是 LangGraph？"},
    stream_mode="updates",
    version="v2",
):
    for node_name, update in chunk["data"].items():
        print(f"[{node_name}] {update}")
