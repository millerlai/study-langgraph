# 8.1 範例：探索替代執行路徑
# 從同一個 checkpoint 建立多個分支，比較不同輸入的結果

"""
探索替代執行路徑：從同一個 checkpoint 建立多個分支
"""
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]


def generate_topic(state: State) -> dict:
    return {"topic": "原始主題"}


def write_joke(state: State) -> dict:
    return {"joke": f"關於「{state['topic']}」的笑話：哈哈！"}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("generate_topic", generate_topic)
    .add_node("write_joke", write_joke)
    .add_edge(START, "generate_topic")
    .add_edge("generate_topic", "write_joke")
    .compile(checkpointer=checkpointer)
)

# 原始執行
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke({}, config)
print(f"原始: {result['joke']}")

# 找到 write_joke 之前的 checkpoint
history = list(graph.get_state_history(config))
before_joke = next(s for s in history if s.next == ("write_joke",))

# 從同一個 checkpoint 建立多個分支
topics = ["貓咪", "程式設計", "咖啡"]
for topic in topics:
    fork_config = graph.update_state(
        before_joke.config,
        values={"topic": topic},
    )
    fork_result = graph.invoke(None, fork_config)
    print(f"分支 [{topic}]: {fork_result['joke']}")
