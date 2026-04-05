# 7.1 範例：使用 RemoveMessage 精準刪除訊息
# 展示從 State 中刪除特定訊息及清空所有訊息的用法

"""
使用 RemoveMessage 從 State 中刪除特定訊息
RemoveMessage 需要搭配 add_messages reducer 使用
"""
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義刪除策略節點
# ============================================================

def delete_old_messages(state: MessagesState) -> dict:
    """刪除最舊的 2 條訊息"""
    messages = state["messages"]
    if len(messages) > 4:
        # 只刪除前 2 條
        to_remove = messages[:2]
        return {"messages": [RemoveMessage(id=m.id) for m in to_remove]}
    return {}

def delete_all_messages(state: MessagesState) -> dict:
    """清空所有訊息歷史"""
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}

def echo(state: MessagesState) -> dict:
    """回聲節點"""
    last = state["messages"][-1]
    return {"messages": [AIMessage(content=f"Echo: {last.content}")]}

# ============================================================
# 2. 建構帶有刪除功能的 Graph
# ============================================================
builder = StateGraph(MessagesState)
builder.add_node("cleanup", delete_old_messages)
builder.add_node("echo", echo)
builder.add_edge(START, "cleanup")
builder.add_edge("cleanup", "echo")
builder.add_edge("echo", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "delete-demo"}}

# ============================================================
# 3. 模擬對話
# ============================================================
for i in range(1, 7):
    result = graph.invoke(
        {"messages": [HumanMessage(content=f"訊息 #{i}")]},
        config,
    )
    msg_count = len(result["messages"])
    print(f"發送第 {i} 條後，剩餘 {msg_count} 條訊息")

# 驗證最終訊息
final = graph.get_state(config)
print("\n--- 最終訊息 ---")
for m in final.values["messages"]:
    print(f"  [{m.type}] {m.content}")
