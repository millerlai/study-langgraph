# 3.1 範例：使用 Command 實現迴圈 + 分支
# 展示使用 Command 原語在節點函數中同時更新 State 和控制路由。

from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command


class LoopState(TypedDict):
    value: int
    log: list[str]


def loop_node(state: LoopState) -> Command[Literal["loop_node", "__end__"]]:
    """使用 Command 同時更新 state 和控制路由"""
    new_value = state["value"] + 1
    log = state.get("log", []) + [f"value={new_value}"]
    print(f"[loop_node] value: {state['value']} -> {new_value}")

    if new_value >= 5:
        # 結束迴圈
        return Command(
            update={"value": new_value, "log": log},
            goto=END,
        )
    else:
        # 繼續迴圈
        return Command(
            update={"value": new_value, "log": log},
            goto="loop_node",
        )


builder = StateGraph(LoopState)
builder.add_node("loop_node", loop_node)
builder.add_edge(START, "loop_node")

graph = builder.compile()

result = graph.invoke({"value": 0, "log": []})
print(f"\n最終 value: {result['value']}")
print(f"log: {result['log']}")
