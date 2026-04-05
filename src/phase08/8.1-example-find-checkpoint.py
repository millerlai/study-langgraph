# 8.1 範例：尋找特定 Checkpoint 的常用方法
# 展示依 next 節點、step 編號、source、最新等方式搜尋 checkpoint

"""
尋找特定 Checkpoint 的常用方法
"""
import uuid
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    steps: Annotated[list[str], add]


def node_a(state: State) -> dict:
    return {"steps": ["A"]}

def node_b(state: State) -> dict:
    return {"steps": ["B"]}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("node_a", node_a)
    .add_node("node_b", node_b)
    .add_edge(START, "node_a")
    .add_edge("node_a", "node_b")
    .add_edge("node_b", END)
    .compile(checkpointer=checkpointer)
)

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
graph.invoke({"steps": []}, config)
history = list(graph.get_state_history(config))

# 方法 1：依 next 節點尋找
before_b = next(s for s in history if s.next == ("node_b",))
print(f"node_b 之前: step={before_b.metadata['step']}")

# 方法 2：依 step 編號尋找
step_1 = next(s for s in history if s.metadata["step"] == 1)
print(f"step 1: next={step_1.next}")

# 方法 3：依 source 尋找 (input/loop/update)
input_cp = next(s for s in history if s.metadata.get("source") == "input")
print(f"input checkpoint: next={input_cp.next}")

# 方法 4：找最後（最新）的 checkpoint
latest = history[0]  # 歷史按時間倒序排列
print(f"最新: step={latest.metadata['step']}, next={latest.next}")
