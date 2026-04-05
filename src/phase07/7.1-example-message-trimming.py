# 7.1 範例：訊息裁剪策略
# 展示使用 RemoveMessage 從 State 中永久刪除舊訊息
# 保留系統訊息 + 最近 N 條對話訊息

"""
訊息裁剪策略：保留系統訊息 + 最近 N 條對話訊息
使用 RemoveMessage 從 LangGraph State 中永久刪除舊訊息
"""
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, RemoveMessage
)
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義 State
# ============================================================
class ChatState(MessagesState):
    summary: str  # 可選的摘要欄位（此範例未使用，留做擴展）

# ============================================================
# 2. 定義裁剪節點
# ============================================================
MAX_MESSAGES = 6  # 最多保留的訊息數量（不含系統訊息）

def trim_messages(state: ChatState) -> dict:
    """裁剪訊息：保留系統訊息 + 最近 MAX_MESSAGES 條"""
    messages = state["messages"]

    # 分離系統訊息和對話訊息
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    non_system_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    if len(non_system_msgs) <= MAX_MESSAGES:
        return {}  # 不需要裁剪

    # 標記要刪除的舊訊息
    msgs_to_remove = non_system_msgs[:-MAX_MESSAGES]
    return {
        "messages": [RemoveMessage(id=m.id) for m in msgs_to_remove]
    }

def chatbot(state: ChatState) -> dict:
    """模擬聊天機器人回覆"""
    messages = state["messages"]
    last_msg = messages[-1]
    reply = f"收到！你說的是「{last_msg.content}」（目前共 {len(messages)} 條訊息）"
    return {"messages": [AIMessage(content=reply)]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(ChatState)
builder.add_node("trim", trim_messages)
builder.add_node("chatbot", chatbot)

builder.add_edge(START, "trim")       # 先裁剪
builder.add_edge("trim", "chatbot")   # 再回覆
builder.add_edge("chatbot", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 4. 模擬長對話
# ============================================================
config = {"configurable": {"thread_id": "trim-demo"}}

# 先加一條系統訊息
graph.invoke(
    {"messages": [
        SystemMessage(content="你是一個友善的助理。"),
        HumanMessage(content="第1條訊息"),
    ]},
    config,
)

# 繼續發送多條訊息
for i in range(2, 8):
    result = graph.invoke(
        {"messages": [HumanMessage(content=f"第{i}條訊息")]},
        config,
    )

# 檢查最終狀態
final_state = graph.get_state(config)
final_messages = final_state.values["messages"]

print(f"最終訊息數量: {len(final_messages)}")
print("--- 剩餘訊息 ---")
for msg in final_messages:
    print(f"  [{msg.type}] {msg.content[:50]}")

# 系統訊息始終保留，非系統訊息最多 MAX_MESSAGES 條
