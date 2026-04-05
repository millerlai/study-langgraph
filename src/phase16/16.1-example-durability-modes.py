# 16.1 範例：Durability Modes 使用
# 展示 exit / async / sync 三種持久化模式
# 需要：pip install langgraph

from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    data: str
    result: str


def process(state: State) -> dict:
    return {"result": f"processed: {state['data']}"}


builder = StateGraph(State)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)


# === "exit" mode ===
# 僅在 graph 完成（成功/失敗/interrupt）時保存
# 最佳效能，但無法從中間節點恢復
result = graph.invoke(
    {"data": "hello"},
    config={"configurable": {"thread_id": "1"}},
    durability="exit",
)

# === "async" mode（預設） ===
# 非同步保存 checkpoint，下一步開始執行時背景寫入
# 良好的效能和持久性平衡
result = graph.invoke(
    {"data": "hello"},
    config={"configurable": {"thread_id": "2"}},
    durability="async",
)

# === "sync" mode ===
# 同步保存 checkpoint，確保每一步都寫入完成後才繼續
# 最高持久性，但有效能開銷
result = graph.invoke(
    {"data": "hello"},
    config={"configurable": {"thread_id": "3"}},
    durability="sync",
)
