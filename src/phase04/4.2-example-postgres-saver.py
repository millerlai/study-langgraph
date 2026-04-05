# 4.2 範例：PostgresSaver（正式環境）
# 展示使用 PostgresSaver 連接 PostgreSQL 進行持久化。
# 注意：需要安裝 langgraph-checkpoint-postgres（uv add langgraph-checkpoint-postgres），
# 且需要一個運行中的 PostgreSQL 資料庫。請修改 DB_URI 為你的實際連線字串。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
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

# === 3. 使用 PostgresSaver ===
DB_URI = "postgresql://user:password@localhost:5432/langgraph_db"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # 首次使用需要建立資料表
    checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "postgres_demo"}}

    r1 = graph.invoke({"messages": ["Hello Postgres"]}, config)
    print(r1["messages"])
    # ['Hello Postgres', 'Echo: Hello Postgres']
