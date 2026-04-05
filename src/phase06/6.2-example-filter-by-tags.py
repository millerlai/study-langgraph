# 6.2 範例：依 LLM 呼叫過濾（tags）
# 展示利用 messages 模式中的 metadata 或 custom 串流的自定義欄位來過濾特定節點的輸出
"""
依 LLM 呼叫過濾 token 串流
利用 messages 模式中的 metadata 來過濾特定節點的 LLM 輸出
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


class State(TypedDict):
    topic: str
    draft: str
    review: str


def draft_node(state: State) -> dict:
    """模擬 LLM 寫初稿（此處用 get_stream_writer 模擬 token 串流）"""
    writer = get_stream_writer()
    # 模擬自定義串流：實際場景中，LLM 的 token 會透過 messages 模式自動串流
    writer({"status": "drafting", "node": "draft_node"})
    return {"draft": f"初稿：{state['topic']} 是一個強大的框架"}


def review_node(state: State) -> dict:
    """模擬 LLM 審稿"""
    writer = get_stream_writer()
    writer({"status": "reviewing", "node": "review_node"})
    return {"review": f"審稿通過：{state['draft']} — 內容正確"}


graph = (
    StateGraph(State)
    .add_node("draft", draft_node)
    .add_node("review", review_node)
    .add_edge(START, "draft")
    .add_edge("draft", "review")
    .add_edge("review", END)
    .compile()
)

# 同時使用 updates + custom 模式，並過濾特定節點的 custom 輸出
print("=== 只顯示 review 節點的 custom 串流 ===")
for chunk in graph.stream(
    {"topic": "LangGraph"},
    stream_mode=["updates", "custom"],
    version="v2",
):
    if chunk["type"] == "custom":
        # 依自定義 metadata 過濾
        if chunk["data"].get("node") == "review_node":
            print(f"  審稿狀態: {chunk['data']}")
    elif chunk["type"] == "updates":
        for node_name, update in chunk["data"].items():
            if node_name == "review":
                print(f"  審稿結果: {update}")
