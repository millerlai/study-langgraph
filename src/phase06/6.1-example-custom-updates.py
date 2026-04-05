# 6.1 範例：custom + updates 同時串流
# 展示同時啟用多種串流模式，用 chunk["type"] 區分來源
"""
同時串流 custom 進度和 updates State 變化
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

class State(TypedDict):
    topic: str
    joke: str

def generate_joke(state: State) -> dict:
    writer = get_stream_writer()
    writer({"step": "thinking", "message": "正在想笑話..."})
    joke = f"為什麼 {state['topic']} 不會迷路？因為它總是跟著 Graph！"
    writer({"step": "done", "message": "想到了！"})
    return {"joke": joke}

graph = (
    StateGraph(State)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)

# 同時啟用多種模式
print("=== custom + updates 同時串流 ===")
for chunk in graph.stream(
    {"topic": "AI Agent", "joke": ""},
    stream_mode=["custom", "updates"],
    version="v2",
):
    if chunk["type"] == "custom":
        print(f"  [進度] {chunk['data']['message']}")
    elif chunk["type"] == "updates":
        for node, update in chunk["data"].items():
            print(f"  [更新] {node}: {update}")

# [進度] 正在想笑話...
# [進度] 想到了！
# [更新] generate_joke: {'joke': '為什麼 AI Agent 不會迷路？因為它總是跟著 Graph！'}
