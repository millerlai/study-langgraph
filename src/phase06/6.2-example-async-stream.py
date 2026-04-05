# 6.2 範例：非同步串流 astream()
# 展示使用 async for + astream() 來逐步接收串流輸出
"""
非同步串流 astream()
使用 async for 來逐步接收串流輸出
"""
import asyncio
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


class State(TypedDict):
    question: str
    answer: str


def think(state: State) -> dict:
    writer = get_stream_writer()
    writer({"status": "思考中..."})
    return {"answer": f"關於「{state['question']}」的回答：LangGraph 很棒！"}


graph = (
    StateGraph(State)
    .add_node("think", think)
    .add_edge(START, "think")
    .add_edge("think", END)
    .compile()
)


async def main():
    print("=== 非同步串流 astream() ===")
    async for chunk in graph.astream(
        {"question": "什麼是 LangGraph？"},
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        if chunk["type"] == "custom":
            print(f"  [狀態] {chunk['data']}")
        elif chunk["type"] == "updates":
            for node_name, update in chunk["data"].items():
                print(f"  [結果] {node_name}: {update}")


# 執行非同步函式
asyncio.run(main())
