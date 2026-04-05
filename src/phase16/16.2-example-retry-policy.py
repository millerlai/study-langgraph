# 16.2 範例：Retry Policy 完整使用
# 展示不同 node 使用不同的重試策略
# 需要：pip install langgraph

import random
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    messages: Annotated[list[str], add]
    api_result: str
    db_result: str


# === 模擬可能失敗的 API 呼叫 ===
api_attempts = 0

def call_external_api(state: State) -> dict:
    """模擬不穩定的外部 API"""
    global api_attempts
    api_attempts += 1
    print(f"  API 呼叫 (attempt {api_attempts})")

    if api_attempts < 3:
        raise ConnectionError("API timeout!")

    return {
        "api_result": "API 回應成功",
        "messages": ["API 呼叫完成"],
    }


# === 模擬可能失敗的 DB 操作 ===
db_attempts = 0

def save_to_database(state: State) -> dict:
    """模擬不穩定的資料庫寫入"""
    global db_attempts
    db_attempts += 1
    print(f"  DB 寫入 (attempt {db_attempts})")

    if db_attempts < 2:
        raise TimeoutError("Database connection lost!")

    return {
        "db_result": "DB 寫入成功",
        "messages": ["DB 操作完成"],
    }


def final_step(state: State) -> dict:
    return {"messages": [f"完成！API: {state['api_result']}, DB: {state['db_result']}"]}


# === 建構 Graph，為不同 node 設定不同的重試策略 ===
builder = StateGraph(State)

# API 呼叫：較多重試次數，指數退避
builder.add_node(
    "call_api",
    call_external_api,
    retry_policy=RetryPolicy(
        max_attempts=5,
        initial_interval=1.0,
        backoff_factor=2.0,
    ),
)

# DB 操作：較少重試，快速重試
builder.add_node(
    "save_db",
    save_to_database,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=0.5,
        backoff_factor=1.5,
    ),
)

# 最終步驟：不需要重試
builder.add_node("final", final_step)

builder.add_edge(START, "call_api")
builder.add_edge("call_api", "save_db")
builder.add_edge("save_db", "final")
builder.add_edge("final", END)

graph = builder.compile(checkpointer=InMemorySaver())

# === 執行 ===
if __name__ == "__main__":
    result = graph.invoke(
        {"messages": ["開始"], "api_result": "", "db_result": ""},
        config={"configurable": {"thread_id": "retry-test-1"}},
    )
    print(f"\n最終結果: {result['messages']}")
    print(f"API 嘗試次數: {api_attempts}")
    print(f"DB 嘗試次數: {db_attempts}")
