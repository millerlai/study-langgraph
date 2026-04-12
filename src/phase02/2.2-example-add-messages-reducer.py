# 2.2 Reducer 機制 — add_messages Reducer 的完整行為展示
# 展示追加、更新同 ID、刪除訊息等操作
# 不需要 API key

"""
add_messages Reducer 的完整行為展示
"""
from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# ============================================================
# 1. 定義 State
# ============================================================
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# ============================================================
# 2. 行為一：追加新訊息
# ============================================================
def add_greeting(state: State) -> dict:
    """追加一則新的 AI 訊息"""
    return {"messages": [AIMessage(content="你好！我是 AI 助手。")]}

# ============================================================
# 3. 行為二：更新同 ID 訊息
# ============================================================
def update_message(state: State) -> dict:
    """更新已存在的訊息（透過 ID 匹配）"""
    # 找到最後一則 AI 訊息的 ID
    last_ai_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break

    if last_ai_msg and last_ai_msg.id:
        # 回傳同 ID 的訊息 → add_messages 會更新而非追加
        return {"messages": [AIMessage(
            id=last_ai_msg.id,
            content="你好！我是升級版 AI 助手。（已更新）"
        )]}
    return {}

# ============================================================
# 4. 行為三：刪除訊息
# ============================================================
def cleanup_messages(state: State) -> dict:
    """刪除指定訊息"""
    # RemoveMessage 會移除指定 ID 的訊息
    msgs_to_remove = []
    for msg in state["messages"]:
        if hasattr(msg, "content") and "系統" in msg.content:
            msgs_to_remove.append(RemoveMessage(id=msg.id))
    return {"messages": msgs_to_remove} if msgs_to_remove else {}

# ============================================================
# 5. 建構與執行
# ============================================================
builder = StateGraph(State)
builder.add_node("greet", add_greeting)
builder.add_node("update", update_message)
builder.add_node("cleanup", cleanup_messages)
builder.add_edge(START, "greet")
builder.add_edge("greet", "update")
builder.add_edge("update", "cleanup")
builder.add_edge("cleanup", END)

graph = builder.compile()

result = graph.invoke({
    "messages": [
        HumanMessage(content="嗨！"),
        HumanMessage(content="系統通知：這是測試訊息"),
    ]
})

for msg in result["messages"]:
    print(f"{msg.type}: {msg.content}")
# human: 嗨！
# ai: 你好！我是升級版 AI 助手。（已更新）   ← 被更新而非追加
# 注意：「系統通知：這是測試訊息」已被 cleanup 刪除
