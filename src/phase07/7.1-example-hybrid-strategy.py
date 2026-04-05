# 7.1 範例：混合策略 — 裁剪訊息 + 在獨立欄位中保留關鍵資訊
# 不需要額外 LLM 呼叫，但能保留重要上下文

"""
混合策略：裁剪訊息 + 在獨立欄位中保留關鍵資訊
不需要額外 LLM 呼叫，但能保留重要上下文
"""
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. State 包含結構化的關鍵資訊欄位
# ============================================================
class HybridState(MessagesState):
    user_facts: Annotated[list[str], add]  # 累積的使用者資訊
    topic_history: Annotated[list[str], add]  # 話題歷史

MAX_MESSAGES = 6

# ============================================================
# 2. 節點
# ============================================================
def extract_and_trim(state: HybridState) -> dict:
    """提取關鍵資訊 + 裁剪舊訊息"""
    messages = state["messages"]
    updates: dict = {}

    # 提取關鍵資訊（實際應用中可用 LLM）
    last_msg = messages[-1] if messages else None
    if last_msg and isinstance(last_msg, HumanMessage):
        content = last_msg.content
        if "我叫" in content or "我是" in content:
            updates["user_facts"] = [f"名字相關: {content[:30]}"]
        if "喜歡" in content or "偏好" in content:
            updates["user_facts"] = [f"偏好: {content[:30]}"]

    # 裁剪
    if len(messages) > MAX_MESSAGES:
        to_remove = messages[:len(messages) - MAX_MESSAGES]
        updates["messages"] = [RemoveMessage(id=m.id) for m in to_remove]
        updates["topic_history"] = [f"（裁剪了 {len(to_remove)} 條舊訊息）"]

    return updates

def respond(state: HybridState) -> dict:
    """回覆時利用結構化資訊"""
    messages = state["messages"]
    facts = state.get("user_facts", [])
    topics = state.get("topic_history", [])

    context_parts = []
    if facts:
        context_parts.append(f"已知: {'; '.join(facts[-3:])}")
    if topics:
        context_parts.append(f"話題: {'; '.join(topics[-3:])}")

    context = " | ".join(context_parts) if context_parts else "無額外上下文"
    last_msg = messages[-1]

    return {
        "messages": [
            AIMessage(content=f"[{context}] 回覆：{last_msg.content}")
        ]
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(HybridState)
builder.add_node("extract_and_trim", extract_and_trim)
builder.add_node("respond", respond)
builder.add_edge(START, "extract_and_trim")
builder.add_edge("extract_and_trim", "respond")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=InMemorySaver())

# ============================================================
# 4. 執行
# ============================================================
config = {"configurable": {"thread_id": "hybrid-demo"}}

test_messages = [
    "你好，我叫小明",
    "我喜歡吃日本料理",
    "推薦台北的餐廳",
    "價位呢？",
    "營業時間？",
    "有外送嗎？",
    "我還喜歡甜點",
    "推薦甜點店",
]

for msg in test_messages:
    result = graph.invoke(
        {"messages": [HumanMessage(content=msg)]},
        config,
    )
    state = graph.get_state(config)
    print(f"訊息數: {len(state.values['messages'])}, "
          f"已知事實: {state.values.get('user_facts', [])}")
