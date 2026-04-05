# 7.2 範例：整合三種記憶類型
# - 語意記憶（Semantic）：使用者的事實資訊
# - 情節記憶（Episodic）：過去的互動經驗（few-shot）
# - 程序性記憶（Procedural）：Agent 的指令和行為規則

"""
整合三種記憶類型的完整範例
- 語意記憶：使用者的事實資訊
- 情節記憶：過去的互動經驗（few-shot）
- 程序性記憶：Agent 的指令和行為規則
"""
import uuid
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, AIMessage

# ============================================================
# 1. 初始化 Store 並寫入三種記憶
# ============================================================
store = InMemoryStore()
user_id = "user-001"

# --- 語意記憶 (Semantic) ---
semantic_ns = (user_id, "semantic")
store.put(semantic_ns, "name", {"fact": "使用者叫小明"})
store.put(semantic_ns, "job", {"fact": "使用者是前端工程師"})
store.put(semantic_ns, "food", {"fact": "使用者喜歡義大利菜"})

# --- 情節記憶 (Episodic) ---
episodic_ns = (user_id, "episodic")
store.put(episodic_ns, "ep-001", {
    "input": "幫我寫一個排序演算法",
    "output": "好的，以下是 Quick Sort 的 Python 實作...",
    "feedback": "positive",
})
store.put(episodic_ns, "ep-002", {
    "input": "解釋 React hooks",
    "output": "React Hooks 是...",
    "feedback": "positive",
})

# --- 程序性記憶 (Procedural) ---
procedural_ns = ("agent", "instructions")
store.put(procedural_ns, "main-prompt", {
    "instructions": "你是一個友善的技術助理。回覆要簡潔、附帶程式碼範例。",
    "version": 1,
})

# ============================================================
# 2. 定義 Node
# ============================================================
class AgentState(MessagesState):
    user_id: str

def respond_with_all_memories(state: AgentState, *, store: BaseStore) -> dict:
    """使用三種記憶來生成回覆"""
    uid = state.get("user_id", "anonymous")
    messages = state["messages"]
    last_msg = messages[-1]

    # 讀取程序性記憶（Agent 指令）
    instructions_item = store.get(("agent", "instructions"), "main-prompt")
    instructions = instructions_item.value["instructions"] if instructions_item else ""

    # 讀取語意記憶（使用者事實）
    facts = store.search((uid, "semantic"))
    fact_strs = [f.value["fact"] for f in facts]

    # 讀取情節記憶（過去成功的互動）
    episodes = store.search((uid, "episodic"), limit=3)
    episode_strs = []
    for ep in episodes:
        episode_strs.append(
            f"  Q: {ep.value['input'][:30]}... → 回饋: {ep.value['feedback']}"
        )

    # 組合上下文
    context = f"""
--- Agent 指令 ---
{instructions}

--- 使用者資訊 ---
{chr(10).join(f'- {f}' for f in fact_strs)}

--- 過去互動 ---
{chr(10).join(episode_strs)}

--- 使用者問題 ---
{last_msg.content}
""".strip()

    reply = AIMessage(content=f"[整合三種記憶回覆]\n{context}")
    return {"messages": [reply]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(AgentState)
builder.add_node("respond", respond_with_all_memories)
builder.add_edge(START, "respond")
builder.add_edge("respond", END)

graph = builder.compile(
    checkpointer=InMemorySaver(),
    store=store,
)

# ============================================================
# 4. 執行
# ============================================================
config = {"configurable": {"thread_id": "demo-1"}}
result = graph.invoke(
    {
        "messages": [HumanMessage(content="幫我寫一個 API 呼叫的範例")],
        "user_id": "user-001",
    },
    config,
)

print(result["messages"][-1].content)

# ============================================================
# 5. 更新程序性記憶（Agent 自我改進）
# ============================================================
print("\n=== 更新 Agent 指令 ===")
current = store.get(("agent", "instructions"), "main-prompt")
print(f"更新前: {current.value['instructions']}")

# 基於回饋更新指令
store.put(("agent", "instructions"), "main-prompt", {
    "instructions": "你是一個友善的技術助理。回覆要簡潔、附帶程式碼範例。請優先使用 TypeScript 範例。",
    "version": 2,
})

updated = store.get(("agent", "instructions"), "main-prompt")
print(f"更新後: {updated.value['instructions']}")
