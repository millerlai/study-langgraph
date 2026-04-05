# 8.1 範例：Replay — 從過去的 checkpoint 重新執行
# 展示如何查看 checkpoint 歷史並從特定 checkpoint 重播後續節點

"""
Replay：從過去的 checkpoint 重新執行
"""
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]


def generate_topic(state: State) -> dict:
    print("  [執行] generate_topic")
    return {"topic": "襪子在烘衣機裡"}


def write_joke(state: State) -> dict:
    print("  [執行] write_joke")
    return {"joke": f"為什麼{state['topic']}會消失？因為它們私奔了！"}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("generate_topic", generate_topic)
    .add_node("write_joke", write_joke)
    .add_edge(START, "generate_topic")
    .add_edge("generate_topic", "write_joke")
    .compile(checkpointer=checkpointer)
)

# === 步驟 1：正常執行圖 ===
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
print("=== 原始執行 ===")
result = graph.invoke({}, config)
print(f"  結果: {result}")

# === 步驟 2：查看歷史 checkpoint ===
print("\n=== Checkpoint 歷史 ===")
history = list(graph.get_state_history(config))
for state in history:
    print(f"  next={state.next}, step={state.metadata['step']}, "
          f"checkpoint_id={state.config['configurable']['checkpoint_id'][:12]}...")

# === 步驟 3：找到 write_joke 之前的 checkpoint 並重播 ===
print("\n=== Replay：從 write_joke 之前重播 ===")
before_joke = next(s for s in history if s.next == ("write_joke",))
replay_result = graph.invoke(None, before_joke.config)
print(f"  重播結果: {replay_result}")
