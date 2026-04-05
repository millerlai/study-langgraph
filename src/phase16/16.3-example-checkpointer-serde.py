# 16.3 範例：JsonPlusSerializer 與 Checkpointer 整合
# 展示序列化器如何與 InMemorySaver 配合
# 需要：pip install langgraph

import uuid
from typing import TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


class State(TypedDict):
    message: str
    timestamp: str
    count: int


def process(state: State) -> dict:
    return {
        "message": f"已處理: {state['message']}",
        "timestamp": datetime.now().isoformat(),
        "count": state["count"] + 1,
    }


# 使用預設的 JsonPlusSerializer（InMemorySaver 預設就用它）
checkpointer = InMemorySaver(serde=JsonPlusSerializer())

graph = (
    StateGraph(State)
    .add_node("process", process)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile(checkpointer=checkpointer)
)

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke(
    {"message": "Hello", "timestamp": "", "count": 0},
    config,
)
print(f"結果: {result}")

# 從 checkpoint 恢復
saved_state = graph.get_state(config)
print(f"儲存的 state: {saved_state.values}")
print(f"checkpoint_id: {saved_state.config['configurable']['checkpoint_id']}")
