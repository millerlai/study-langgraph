# 5.2 範例：Time Travel - 回到過去的 Checkpoint
# 展示使用 get_state_history() 取得歷史 checkpoint，並從過去的狀態重新執行
"""
Time Travel：回到過去的 State 重新執行
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

class State(TypedDict):
    value: int
    history: str

def double(state: State) -> dict:
    new_val = state["value"] * 2
    return {"value": new_val, "history": f"{state.get('history', '')} -> double({new_val})"}

def add_ten(state: State) -> dict:
    new_val = state["value"] + 10
    return {"value": new_val, "history": f"{state.get('history', '')} -> add_ten({new_val})"}

builder = StateGraph(State)
builder.add_node("double", double)
builder.add_node("add_ten", add_ten)
builder.add_edge(START, "double")
builder.add_edge("double", "add_ten")
builder.add_edge("add_ten", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "time-travel-1"}}
result = graph.invoke({"value": 5, "history": "start(5)"}, config=config)
print(f"原始結果: value={result['value']}, history={result['history']}")
# 原始結果: value=20, history=start(5) -> double(10) -> add_ten(20)

# ============================================================
# 取得歷史 checkpoint
# ============================================================
print("\n=== 歷史 Checkpoints ===")
for state in graph.get_state_history(config):
    print(f"  checkpoint_id={state.config['configurable'].get('checkpoint_id', 'N/A')}, "
          f"value={state.values.get('value', '?')}, "
          f"next={state.next}")

# 找到 double 執行完、add_ten 還沒開始的 checkpoint
# 從那個 checkpoint 重新開始，但改用不同的初始值
for state in graph.get_state_history(config):
    if state.next == ("add_ten",):
        # 找到了！從這裡開始，但先修改 value
        replay_config = state.config
        graph.update_state(replay_config, values={"value": 100})
        result = graph.invoke(None, config=replay_config)
        print(f"\n重播結果: value={result['value']}")
        # 重播結果: value=110  (100 + 10)
        break
