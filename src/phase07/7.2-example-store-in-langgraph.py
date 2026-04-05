# 7.2 範例：在 LangGraph 中整合 Store（長期記憶）
# 機器人能在不同 Thread 中記住使用者資訊

"""
在 LangGraph 中整合 Store（長期記憶）
機器人能在不同 Thread 中記住使用者資訊
"""
import uuid
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

# ============================================================
# 1. 定義 State
# ============================================================
class ChatState(MessagesState):
    user_id: str  # 用來定位長期記憶的使用者 ID

# ============================================================
# 2. 定義 Nodes（透過 store 參數存取長期記憶）
# ============================================================

def extract_memories(state: ChatState, *, store: BaseStore) -> dict:
    """
    從對話中提取資訊並存入長期記憶
    store 參數由 LangGraph 自動注入
    """
    user_id = state.get("user_id", "anonymous")
    namespace = (user_id, "memories")
    messages = state["messages"]
    last_msg = messages[-1]

    if not isinstance(last_msg, HumanMessage):
        return {}

    content = last_msg.content

    # 簡單的資訊提取（實際應用中用 LLM）
    extracted = []
    if "我叫" in content or "我是" in content:
        extracted.append({"type": "name", "content": content})
    if "喜歡" in content:
        extracted.append({"type": "preference", "content": content})
    if "住在" in content or "在" in content and "工作" in content:
        extracted.append({"type": "location", "content": content})

    # 存入 Store
    for info in extracted:
        mem_id = str(uuid.uuid4())
        store.put(namespace, mem_id, info)

    return {}

def respond_with_memory(state: ChatState, *, store: BaseStore) -> dict:
    """
    回覆時從長期記憶中讀取使用者資訊
    """
    user_id = state.get("user_id", "anonymous")
    namespace = (user_id, "memories")

    # 從 Store 搜尋記憶
    memories = store.search(namespace, limit=5)
    memory_context = ""
    if memories:
        mem_strs = [m.value.get("content", "") for m in memories]
        memory_context = f"\n[長期記憶] {'; '.join(mem_strs)}"

    messages = state["messages"]
    last_msg = messages[-1]

    reply = f"收到：「{last_msg.content}」{memory_context}"
    return {"messages": [AIMessage(content=reply)]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(ChatState)
builder.add_node("extract", extract_memories)
builder.add_node("respond", respond_with_memory)
builder.add_edge(START, "extract")
builder.add_edge("extract", "respond")
builder.add_edge("respond", END)

# 同時設定 checkpointer 和 store
checkpointer = InMemorySaver()
memory_store = InMemoryStore()

graph = builder.compile(
    checkpointer=checkpointer,
    store=memory_store,
)

# ============================================================
# 4. Thread 1：使用者自我介紹
# ============================================================
config_t1 = {"configurable": {"thread_id": "thread-1"}}

result = graph.invoke(
    {
        "messages": [HumanMessage(content="你好，我叫小明，我喜歡攝影")],
        "user_id": "user-001",
    },
    config_t1,
)
print("Thread-1 回覆:", result["messages"][-1].content)

# ============================================================
# 5. Thread 2：新對話，但仍能存取同一使用者的記憶
# ============================================================
config_t2 = {"configurable": {"thread_id": "thread-2"}}

result = graph.invoke(
    {
        "messages": [HumanMessage(content="推薦一些活動給我")],
        "user_id": "user-001",  # 同一個使用者
    },
    config_t2,
)
print("Thread-2 回覆:", result["messages"][-1].content)
# 回覆中會包含 Thread-1 中提取的長期記憶！

# ============================================================
# 6. 不同使用者看不到彼此的記憶
# ============================================================
config_t3 = {"configurable": {"thread_id": "thread-3"}}

result = graph.invoke(
    {
        "messages": [HumanMessage(content="你知道什麼關於我的資訊？")],
        "user_id": "user-002",  # 不同使用者
    },
    config_t3,
)
print("Thread-3 (user-002) 回覆:", result["messages"][-1].content)
# 沒有 user-001 的記憶

# ============================================================
# 7. 查看 Store 內容
# ============================================================
print("\n=== Store 中的記憶 ===")
for user in ["user-001", "user-002"]:
    mems = memory_store.search((user, "memories"))
    print(f"{user}: {len(mems)} 筆記憶")
    for m in mems:
        print(f"  - [{m.value.get('type', '?')}] {m.value.get('content', '')[:50]}")
