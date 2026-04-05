# 4.3 範例：update_state 更新 State 建立新 Checkpoint
# 展示手動修改 State 並從特定 checkpoint 分支繼續執行。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State 和節點 ===
class State(TypedDict):
    topic: str
    joke: str
    edits: Annotated[list[str], add]

def generate_topic(state: State) -> dict:
    return {"topic": "程式設計", "edits": ["topic_generated"]}

def write_joke(state: State) -> dict:
    topic = state["topic"]
    return {"joke": f"為什麼 {topic} 很有趣？因為它充滿 bug！", "edits": ["joke_written"]}

# === 2. 建構圖 ===
builder = StateGraph(State)
builder.add_node("generate_topic", generate_topic)
builder.add_node("write_joke", write_joke)
builder.add_edge(START, "generate_topic")
builder.add_edge("generate_topic", "write_joke")
builder.add_edge("write_joke", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 3. 第一次執行 ===
config = {"configurable": {"thread_id": "update_demo"}}
result = graph.invoke({"topic": "", "joke": "", "edits": []}, config)
print(f"原始結果: {result['joke']}")
# 原始結果: 為什麼 程式設計 很有趣？因為它充滿 bug！

# === 4. 找到 write_joke 執行前的 checkpoint ===
history = list(graph.get_state_history(config))
before_joke = next(s for s in history if s.next == ("write_joke",))
print(f"write_joke 前的 topic: {before_joke.values['topic']}")
# write_joke 前的 topic: 程式設計

# === 5. 用 update_state 修改 topic，建立分支 ===
fork_config = graph.update_state(
    before_joke.config,
    values={"topic": "AI 咖啡機"},  # 修改 topic
)

# === 6. 從分支繼續執行 ===
fork_result = graph.invoke(None, fork_config)
print(f"分支結果: {fork_result['joke']}")
# 分支結果: 為什麼 AI 咖啡機 很有趣？因為它充滿 bug！

# === 7. 驗證原始歷史仍在 ===
print(f"分支的 edits: {fork_result['edits']}")
# 分支的 edits: ['topic_generated', 'joke_written']
