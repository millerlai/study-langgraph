# 4.2 範例：SqliteSaver（本地持久化）
# 展示使用 SqliteSaver 將 checkpoint 儲存到 SQLite 資料庫檔案。
# 注意：需要安裝 langgraph-checkpoint-sqlite（uv add langgraph-checkpoint-sqlite）。

import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
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

# === 3. 使用 SqliteSaver（以 context manager 管理連線） ===
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "sqlite_demo"}}

    # 第一次執行
    r1 = graph.invoke({"messages": ["第一次"]}, config)
    print(r1["messages"])
    # ['第一次', 'Echo: 第一次']

    # 第二次執行（接續）
    r2 = graph.invoke({"messages": ["第二次"]}, config)
    print(r2["messages"])
    # ['第一次', 'Echo: 第一次', '第二次', 'Echo: 第二次']

# === 4. 也可以直接傳入 sqlite3 連線 ===
conn = sqlite3.connect("checkpoints.db")
checkpointer = SqliteSaver(conn)
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "sqlite_demo"}}
state = graph.get_state(config)
print(f"之前的訊息仍在: {state.values['messages']}")
# 之前的訊息仍在: ['第一次', 'Echo: 第一次', '第二次', 'Echo: 第二次']

conn.close()
