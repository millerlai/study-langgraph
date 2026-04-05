# 4.2 範例：InMemorySaver（開發用）
# 展示使用 InMemorySaver 進行多輪對話的基本用法。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State ===
class ChatState(TypedDict):
    messages: Annotated[list[str], add]
    summary: str

# === 2. 定義節點 ===
def chat_node(state: ChatState) -> dict:
    last_msg = state["messages"][-1]
    reply = f"你說了: {last_msg}"
    return {"messages": [reply]}

def summarize_node(state: ChatState) -> dict:
    return {"summary": f"共 {len(state['messages'])} 則訊息"}

# === 3. 建構圖 ===
builder = StateGraph(ChatState)
builder.add_node("chat", chat_node)
builder.add_node("summarize", summarize_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", "summarize")
builder.add_edge("summarize", END)

# === 4. 使用 InMemorySaver 編譯 ===
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 5. 執行多輪對話 ===
config = {"configurable": {"thread_id": "demo_001"}}

# 第一輪
result1 = graph.invoke({"messages": ["你好"], "summary": ""}, config)
print(f"第一輪: {result1['messages']}")
print(f"摘要:   {result1['summary']}")
# 第一輪: ['你好', '你說了: 你好']
# 摘要:   共 2 則訊息

# 第二輪（接續上次的 State）
result2 = graph.invoke({"messages": ["今天天氣如何？"]}, config)
print(f"第二輪: {result2['messages']}")
print(f"摘要:   {result2['summary']}")
# 第二輪: ['你好', '你說了: 你好', '今天天氣如何？', '你說了: 今天天氣如何？']
# 摘要:   共 4 則訊息
