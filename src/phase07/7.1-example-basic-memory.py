# 7.1 範例：透過 Checkpointer 實現基本對話記憶
# 展示 InMemorySaver 如何在同一 thread_id 內保留對話歷史
# 不同 thread_id 之間的記憶互相獨立

"""
透過 Checkpointer 實現基本對話記憶
每次呼叫 graph.invoke 都能保留先前的對話歷史
"""
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義 State（使用內建 MessagesState）
# ============================================================
# MessagesState 等同：
# class MessagesState(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]

# ============================================================
# 2. 定義 Node
# ============================================================
def chatbot(state: MessagesState) -> dict:
    """簡單的回聲機器人，示範記憶效果"""
    messages = state["messages"]
    last_msg = messages[-1]

    # 檢查歷史訊息中是否有自我介紹
    user_name = None
    for msg in messages:
        if hasattr(msg, "content") and "我叫" in str(msg.content):
            # 簡單提取名字
            content = str(msg.content)
            idx = content.index("我叫") + 2
            user_name = content[idx:].strip().rstrip("。！!.")

    greeting = f"，{user_name}" if user_name else ""
    response_text = f"你好{greeting}！你說的是：「{last_msg.content}」"

    return {"messages": [{"role": "assistant", "content": response_text}]}

# ============================================================
# 3. 建構 Graph + Checkpointer
# ============================================================
builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# 關鍵：指定 checkpointer
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 4. 模擬多輪對話
# ============================================================
config = {"configurable": {"thread_id": "user-001"}}

# 第一輪
result1 = graph.invoke(
    {"messages": [{"role": "user", "content": "我叫小明"}]},
    config,
)
print("第一輪回覆:", result1["messages"][-1].content)
# 第一輪回覆: 你好，小明！你說的是：「我叫小明」

# 第二輪（同一 thread_id，保留記憶）
result2 = graph.invoke(
    {"messages": [{"role": "user", "content": "你還記得我嗎？"}]},
    config,
)
print("第二輪回覆:", result2["messages"][-1].content)
# 第二輪回覆: 你好，小明！你說的是：「你還記得我嗎？」

# 不同的 thread_id → 沒有記憶
config2 = {"configurable": {"thread_id": "user-002"}}
result3 = graph.invoke(
    {"messages": [{"role": "user", "content": "你還記得我嗎？"}]},
    config2,
)
print("新線程回覆:", result3["messages"][-1].content)
# 新線程回覆: 你好！你說的是：「你還記得我嗎？」

# ============================================================
# 5. 查看 Checkpoint 歷史
# ============================================================
history = list(graph.get_state_history(config))
print(f"\n線程 user-001 共有 {len(history)} 個 checkpoints")
for i, snapshot in enumerate(history):
    print(f"  [{i}] step={snapshot.metadata.get('step', '?')}, "
          f"next={snapshot.next}, "
          f"messages_count={len(snapshot.values.get('messages', []))}")
