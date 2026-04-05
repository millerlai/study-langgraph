# 8.1 範例：Fork — 從過去的 checkpoint 分支，修改 state 後繼續
# 展示如何修改歷史狀態並從修改後的狀態繼續執行，原始歷史不受影響

"""
Fork：從過去的 checkpoint 分支，修改 state 後繼續
"""
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]


def generate_topic(state: State) -> dict:
    return {"topic": "襪子在烘衣機裡"}


def write_joke(state: State) -> dict:
    return {"joke": f"為什麼{state['topic']}很有趣？因為每次都有驚喜！"}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("generate_topic", generate_topic)
    .add_node("write_joke", write_joke)
    .add_edge(START, "generate_topic")
    .add_edge("generate_topic", "write_joke")
    .compile(checkpointer=checkpointer)
)

# 正常執行
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke({}, config)
print(f"原始結果: {result}")

# 找到 write_joke 之前的 checkpoint
history = list(graph.get_state_history(config))
before_joke = next(s for s in history if s.next == ("write_joke",))

# Fork：修改 topic 為 "小雞"
fork_config = graph.update_state(
    before_joke.config,
    values={"topic": "小雞"},
)

# 從 Fork 點繼續執行
fork_result = graph.invoke(None, fork_config)
print(f"Fork 結果: {fork_result}")

# 原始結果不受影響
original = graph.get_state(config)
print(f"原始 state: {original.values}")
