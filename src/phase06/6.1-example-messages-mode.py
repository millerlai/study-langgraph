# 6.1 範例：messages 模式 - 串流 LLM token
# 展示 stream_mode="messages" 用來串流 LLM 生成的 token 和 metadata
# 注意：需要安裝 langchain-core（已包含在 langgraph 依賴中）
"""
messages 模式：串流 LLM token
每個 chunk 包含 (message_chunk, metadata)
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage, AIMessage, AIMessageChunk, HumanMessage
from langgraph.graph import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def chatbot(state: State) -> dict:
    """模擬 LLM 回應（實際應用中這裡會呼叫 ChatModel）"""
    last_msg = state["messages"][-1]
    response = AIMessage(content=f"你問了：{last_msg.content}，這是我的回答。")
    return {"messages": [response]}

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile()

# ============================================================
# messages 模式
# ============================================================
print("=== messages 模式 ===")
for chunk in graph.stream(
    {"messages": [HumanMessage(content="什麼是 LangGraph？")]},
    stream_mode="messages",
    version="v2",
):
    # v2 格式：{"type": "messages", "data": [message_chunk, metadata]}
    if chunk["type"] == "messages":
        msg_chunk, metadata = chunk["data"]
        print(f"  node={metadata.get('langgraph_node', '?')}, "
              f"type={type(msg_chunk).__name__}, "
              f"content={msg_chunk.content[:50]}")

# messages 模式輸出的 metadata 包含：
# - langgraph_node: 產生此 token 的節點名稱
# - langgraph_step: 第幾步
# - langgraph_triggers: 觸發此節點的邊
# - ls_model_name: LLM 模型名稱（如果有的話）
