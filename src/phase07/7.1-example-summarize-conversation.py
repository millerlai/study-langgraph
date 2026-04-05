# 7.1 範例：訊息摘要策略
# 當訊息超過門檻時，用模擬函式生成摘要並替換舊訊息
# 實際應用中可替換為 LLM 呼叫

"""
訊息摘要策略：
當訊息超過門檻時，用 LLM（此範例用模擬函式）生成摘要並替換舊訊息
"""
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, RemoveMessage
)
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義 State（擴展 MessagesState 加入 summary 欄位）
# ============================================================
class SummarizableState(MessagesState):
    summary: str  # 累積的對話摘要

# ============================================================
# 2. 定義節點
# ============================================================
SUMMARY_THRESHOLD = 6  # 超過此數量觸發摘要

def should_summarize(state: SummarizableState) -> str:
    """條件路由：決定是否需要摘要"""
    messages = state["messages"]
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]
    if len(non_system) > SUMMARY_THRESHOLD:
        return "summarize"
    return "respond"

def summarize_conversation(state: SummarizableState) -> dict:
    """
    摘要節點：將舊訊息濃縮為摘要
    實際應用中應使用 LLM 來生成摘要
    """
    messages = state["messages"]
    existing_summary = state.get("summary", "")

    # 分離系統訊息和對話訊息
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]

    # 保留最近 4 條，其餘做摘要
    to_summarize = non_system[:-4]
    to_keep = non_system[-4:]

    # === 模擬 LLM 生成摘要 ===
    # 實際應用中替換為：
    # summary = llm.invoke(f"請摘要以下對話：\n{to_summarize}\n\n先前摘要：{existing_summary}")
    summary_parts = []
    if existing_summary:
        summary_parts.append(existing_summary)
    for msg in to_summarize:
        role = "使用者" if isinstance(msg, HumanMessage) else "助理"
        summary_parts.append(f"{role}：{msg.content[:30]}")

    new_summary = "；".join(summary_parts)

    # 刪除舊訊息
    remove_msgs = [RemoveMessage(id=m.id) for m in to_summarize]

    return {
        "messages": remove_msgs,
        "summary": new_summary,
    }

def respond(state: SummarizableState) -> dict:
    """回覆節點：帶入摘要上下文"""
    messages = state["messages"]
    summary = state.get("summary", "")
    last_msg = messages[-1]

    # 組合摘要上下文
    context = f"[摘要: {summary}] " if summary else ""
    reply = f"{context}你說：「{last_msg.content}」"

    return {"messages": [AIMessage(content=reply)]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(SummarizableState)
builder.add_node("summarize", summarize_conversation)
builder.add_node("respond", respond)

# 從 START 根據條件決定路徑
builder.add_conditional_edges(
    START,
    should_summarize,
    {"summarize": "summarize", "respond": "respond"},
)
builder.add_edge("summarize", "respond")
builder.add_edge("respond", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 4. 模擬長對話
# ============================================================
config = {"configurable": {"thread_id": "summary-demo"}}

conversations = [
    "你好，我是小明",
    "台北天氣如何？",
    "推薦一家餐廳",
    "地址在哪裡？",
    "營業時間呢？",
    "有停車場嗎？",
    "價位大概多少？",
    "需要預約嗎？",
]

for i, msg in enumerate(conversations):
    result = graph.invoke(
        {"messages": [HumanMessage(content=msg)]},
        config,
    )
    state = graph.get_state(config)
    msg_count = len(state.values["messages"])
    summary = state.values.get("summary", "（無）")
    print(f"[{i+1}] 訊息數: {msg_count}, 摘要: {summary[:60]}")

print("\n--- 最終訊息 ---")
final = graph.get_state(config)
for m in final.values["messages"]:
    print(f"  [{m.type}] {m.content[:80]}")
