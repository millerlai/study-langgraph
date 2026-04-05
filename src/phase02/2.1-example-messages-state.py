# 2.1 State Schema 設計 — 使用 MessagesState 建構聊天機器人
# 展示 MessagesState 的繼承擴展與 add_messages reducer
# 不需要 API key（使用模擬邏輯）

"""
使用 MessagesState 建構聊天機器人
"""
from langgraph.graph import StateGraph, MessagesState, START, END

# ============================================================
# 1. 擴展 MessagesState
# ============================================================
class ChatState(MessagesState):
    user_name: str        # 使用者名稱
    topic: str            # 對話主題

# ============================================================
# 2. 定義 Nodes
# ============================================================
def greet(state: ChatState) -> dict:
    """歡迎節點"""
    name = state.get("user_name", "使用者")
    return {
        "messages": [{"role": "assistant", "content": f"你好，{name}！"}],
        "topic": "greeting",
    }

def respond(state: ChatState) -> dict:
    """回應節點"""
    last_user_msg = state["messages"][-1]
    return {
        "messages": [{"role": "assistant", "content": f"收到你的訊息：{last_user_msg.content}"}],
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(ChatState)
builder.add_node("greet", greet)
builder.add_node("respond", respond)
builder.add_edge(START, "greet")
builder.add_edge("greet", "respond")
builder.add_edge("respond", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({
    "messages": [{"role": "user", "content": "請幫我分析資料"}],
    "user_name": "小明",
    "topic": "",
})

for msg in result["messages"]:
    print(f"{msg.type}: {msg.content}")
# human: 請幫我分析資料
# ai: 你好，小明！
# ai: 收到你的訊息：請幫我分析資料
