# 4.3 範例：完整的 State 操作工作流
# 綜合展示執行圖、查看歷史、從特定 checkpoint 分支、恢復執行的完整工作流。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# =============================================
# 綜合範例：文章撰寫工作流
# 流程：選題 → 撰寫初稿 → 審校
# =============================================

# === 1. 定義 State ===
class ArticleState(TypedDict):
    topic: str
    draft: str
    review: str
    log: Annotated[list[str], add]

# === 2. 定義節點 ===
def choose_topic(state: ArticleState) -> dict:
    return {
        "topic": "LangGraph 入門",
        "log": ["[choose_topic] 選定主題: LangGraph 入門"]
    }

def write_draft(state: ArticleState) -> dict:
    topic = state["topic"]
    draft = f"《{topic}》\n\nLangGraph 是一個強大的框架..."
    return {
        "draft": draft,
        "log": [f"[write_draft] 撰寫關於 '{topic}' 的初稿"]
    }

def review_draft(state: ArticleState) -> dict:
    return {
        "review": "審校通過，內容品質良好。",
        "log": ["[review_draft] 審校完成"]
    }

# === 3. 建構圖 ===
builder = StateGraph(ArticleState)
builder.add_node("choose_topic", choose_topic)
builder.add_node("write_draft", write_draft)
builder.add_node("review_draft", review_draft)
builder.add_edge(START, "choose_topic")
builder.add_edge("choose_topic", "write_draft")
builder.add_edge("write_draft", "review_draft")
builder.add_edge("review_draft", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 4. 執行工作流 ===
config = {"configurable": {"thread_id": "article_001"}}
result = graph.invoke(
    {"topic": "", "draft": "", "review": "", "log": []},
    config
)

print("=== 執行結果 ===")
print(f"主題: {result['topic']}")
print(f"初稿: {result['draft'][:30]}...")
print(f"審校: {result['review']}")
print(f"日誌: {result['log']}")
print()

# === 5. 查看完整歷史 ===
print("=== 完整歷史 ===")
history = list(graph.get_state_history(config))
for i, state in enumerate(history):
    step = state.metadata["step"]
    source = state.metadata["source"]
    next_nodes = state.next
    print(f"[{i}] step={step}, source={source}, next={next_nodes}")

print()

# === 6. 找到撰寫初稿前的 checkpoint ===
before_draft = next(s for s in history if s.next == ("write_draft",))
print(f"=== 撰寫初稿前的 State ===")
print(f"topic: {before_draft.values['topic']}")
print(f"draft: '{before_draft.values['draft']}'  (還是空的)")
print()

# === 7. 修改主題後分支 ===
fork_config = graph.update_state(
    before_draft.config,
    values={"topic": "LangGraph 進階技巧"},
    as_node="choose_topic",  # 假裝是 choose_topic 產生的
)

# === 8. 從分支繼續執行 ===
fork_result = graph.invoke(None, fork_config)
print("=== 分支結果 ===")
print(f"主題: {fork_result['topic']}")
print(f"初稿: {fork_result['draft'][:40]}...")
print()

# === 9. 驗證原始結果和分支結果並存 ===
print("=== 驗證：查看更新後的歷史 ===")
updated_history = list(graph.get_state_history(config))
print(f"原始歷史有 {len(history)} 個 checkpoint")
print(f"更新後有   {len(updated_history)} 個 checkpoint")

# 找到所有 source="update" 的 checkpoint
updates = [s for s in updated_history if s.metadata["source"] == "update"]
print(f"其中手動更新的: {len(updates)} 個")

# === 10. 取得目前最新 State（是分支的結果） ===
latest = graph.get_state(config)
print(f"\n最新 State 的主題: {latest.values['topic']}")
print(f"最新 State 的審校: {latest.values['review']}")
