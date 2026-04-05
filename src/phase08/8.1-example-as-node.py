# 8.1 範例：使用 as_node 控制 Fork 後的執行起點
# 展示 update_state 的 as_node 參數如何影響後續節點執行

"""
使用 as_node 控制 Fork 後的執行起點
"""
import uuid
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    steps: Annotated[list[str], add]


def step_a(state: State) -> dict:
    return {"steps": ["A 完成"]}


def step_b(state: State) -> dict:
    return {"steps": ["B 完成"]}


def step_c(state: State) -> dict:
    return {"steps": ["C 完成"]}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("step_a", step_a)
    .add_node("step_b", step_b)
    .add_node("step_c", step_c)
    .add_edge(START, "step_a")
    .add_edge("step_a", "step_b")
    .add_edge("step_b", "step_c")
    .add_edge("step_c", END)
    .compile(checkpointer=checkpointer)
)

# 正常執行
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke({"steps": ["開始"]}, config)
print(f"原始結果: {result['steps']}")

# 找到 step_b 之前的 checkpoint
history = list(graph.get_state_history(config))
before_b = next(s for s in history if s.next == ("step_b",))

# Fork：插入自定義步驟，當作 step_b 的輸出
fork_config = graph.update_state(
    before_b.config,
    values={"steps": ["自定義 B 完成"]},
    as_node="step_b",  # 當作 step_b 已執行
)

# 從 fork 繼續 — 只有 step_c 會執行
fork_result = graph.invoke(None, fork_config)
print(f"Fork 結果: {fork_result['steps']}")
