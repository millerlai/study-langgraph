# 6.1 範例：Stream 基本用法 - v1 vs v2 格式
# 展示 graph.stream() 的 v2 格式（推薦）和 v1 預設格式的差異
"""
Stream 基本用法：v2 格式
v2 格式回傳的 chunk 是 dict，包含 type 和 data
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    topic: str
    joke: str

def generate_joke(state: State) -> dict:
    return {"joke": f"為什麼 {state['topic']} 要去上學？因為它想拿到好成績！"}

graph = (
    StateGraph(State)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)

# ============================================================
# v2 格式：每個 chunk 是 {"type": "...", "data": ...}
# ============================================================
print("=== v2 格式 ===")
for chunk in graph.stream(
    {"topic": "冰淇淋"},
    stream_mode="updates",
    version="v2",
):
    print(f"type={chunk['type']}, data={chunk['data']}")

# type=updates, data={'generate_joke': {'joke': '為什麼冰淇淋要去上學？因為它想拿到好成績！'}}

# ============================================================
# 不指定 version 時的預設格式（v1 相容模式）
# ============================================================
print("\n=== v1 格式（預設）===")
for chunk in graph.stream(
    {"topic": "冰淇淋"},
    stream_mode="updates",
):
    print(f"chunk={chunk}")

# chunk={'generate_joke': {'joke': '為什麼冰淇淋要去上學？因為它想拿到好成績！'}}
