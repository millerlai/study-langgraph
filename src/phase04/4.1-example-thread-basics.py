# 4.1 範例：Thread 基本用法
# 展示使用 thread_id 進行多輪對話，以及不同 thread 之間的隔離性。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State ===
class ConversationState(TypedDict):
    messages: Annotated[list[str], add]

# === 2. 定義節點 ===
def echo_node(state: ConversationState) -> dict:
    last_msg = state["messages"][-1]
    return {"messages": [f"Echo: {last_msg}"]}

# === 3. 建構並編譯圖（帶 checkpointer） ===
builder = StateGraph(ConversationState)
builder.add_node("echo", echo_node)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 4. 使用 thread_id 進行對話 ===
# 第一次對話
config_thread1 = {"configurable": {"thread_id": "user_alice_001"}}
result1 = graph.invoke({"messages": ["你好"]}, config_thread1)
print(result1["messages"])
# 輸出: ['你好', 'Echo: 你好']

# 同一個 thread 繼續對話——會帶著之前的 State
result2 = graph.invoke({"messages": ["今天天氣如何？"]}, config_thread1)
print(result2["messages"])
# 輸出: ['你好', 'Echo: 你好', '今天天氣如何？', 'Echo: 今天天氣如何？']

# 不同 thread——全新的 State
config_thread2 = {"configurable": {"thread_id": "user_bob_002"}}
result3 = graph.invoke({"messages": ["嗨"]}, config_thread2)
print(result3["messages"])
# 輸出: ['嗨', 'Echo: 嗨']  ← 不包含 Alice 的訊息
