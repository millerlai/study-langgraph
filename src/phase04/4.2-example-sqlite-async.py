# 4.2 範例：AsyncSqliteSaver（非同步用法）
# 展示使用 AsyncSqliteSaver 進行非同步的 checkpoint 儲存。
# 注意：需要安裝 langgraph-checkpoint-sqlite（uv add langgraph-checkpoint-sqlite）。

import asyncio
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State 和節點 ===
class State(TypedDict):
    messages: Annotated[list[str], add]

def echo(state: State) -> dict:
    return {"messages": [f"Echo: {state['messages'][-1]}"]}

# === 2. 建構圖 ===
builder = StateGraph(State)
builder.add_node("echo", echo)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

# === 3. 非同步執行 ===
async def main():
    async with AsyncSqliteSaver.from_conn_string("async_checkpoints.db") as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "async_demo"}}

        r1 = await graph.ainvoke({"messages": ["非同步第一次"]}, config)
        print(r1["messages"])

        r2 = await graph.ainvoke({"messages": ["非同步第二次"]}, config)
        print(r2["messages"])

asyncio.run(main())
