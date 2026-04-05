# 6.2 範例：多模式同時串流
# 展示同時接收 updates（狀態變更）和 custom（自定義事件）的串流
"""
多模式同時串流
同時接收 updates（狀態變更）和 custom（自定義事件）
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


class State(TypedDict):
    text: str
    processed: str


def preprocess(state: State) -> dict:
    writer = get_stream_writer()
    writer({"stage": "preprocessing", "progress": "50%"})
    writer({"stage": "preprocessing", "progress": "100%"})
    return {"processed": state["text"].upper()}


def postprocess(state: State) -> dict:
    writer = get_stream_writer()
    writer({"stage": "postprocessing", "progress": "100%"})
    return {"processed": f"[完成] {state['processed']}"}


graph = (
    StateGraph(State)
    .add_node("preprocess", preprocess)
    .add_node("postprocess", postprocess)
    .add_edge(START, "preprocess")
    .add_edge("preprocess", "postprocess")
    .add_edge("postprocess", END)
    .compile()
)

print("=== 多模式同時串流：updates + custom ===")
for chunk in graph.stream(
    {"text": "hello langgraph"},
    stream_mode=["updates", "custom"],
    version="v2",
):
    if chunk["type"] == "custom":
        print(f"  [進度] {chunk['data']}")
    elif chunk["type"] == "updates":
        for node_name, update in chunk["data"].items():
            print(f"  [狀態] {node_name} => {update}")
