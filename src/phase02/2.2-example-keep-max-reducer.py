# 2.2 Reducer 機制 — 自定義 Reducer：只保留最大值
# 展示如何撰寫自定義 Reducer 函數
# 不需要 API key

"""
自定義 Reducer：只保留最大值
"""
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

def keep_max(current: int, new: int) -> int:
    """只保留較大的值"""
    return max(current, new)

class State(TypedDict):
    high_score: Annotated[int, keep_max]
    player: str

def round_1(state: State) -> dict:
    return {"high_score": 75, "player": "round_1"}

def round_2(state: State) -> dict:
    return {"high_score": 60, "player": "round_2"}  # 60 < 75，不會更新 high_score

def round_3(state: State) -> dict:
    return {"high_score": 90, "player": "round_3"}  # 90 > 75，會更新 high_score

builder = StateGraph(State)
builder.add_node("round_1", round_1)
builder.add_node("round_2", round_2)
builder.add_node("round_3", round_3)
builder.add_edge(START, "round_1")
builder.add_edge("round_1", "round_2")
builder.add_edge("round_2", "round_3")
builder.add_edge("round_3", END)

graph = builder.compile()

result = graph.invoke({"high_score": 0, "player": ""})
print(result)
# {"high_score": 90, "player": "round_3"}
#  high_score 經歷: 0 → 75 → 75(不變) → 90
