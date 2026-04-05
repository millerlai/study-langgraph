# 8.1 範例：除錯與問題回溯
# 使用時間旅行來定位和修復問題，展示 Fork 修正 state 後重新執行

"""
除錯與問題回溯：使用時間旅行來定位和修復問題
"""
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    data: NotRequired[str]
    validated: NotRequired[bool]
    result: NotRequired[str]


def fetch_data(state: State) -> dict:
    return {"data": "raw_data_123"}


def validate_data(state: State) -> dict:
    # 模擬驗證邏輯 — 這裡可能有 bug
    is_valid = state.get("data", "").startswith("raw_data")
    return {"validated": is_valid}


def process_data(state: State) -> dict:
    if not state.get("validated"):
        return {"result": "錯誤：資料未通過驗證"}
    return {"result": f"處理完成：{state['data']}"}


checkpointer = InMemorySaver()
graph = (
    StateGraph(State)
    .add_node("fetch", fetch_data)
    .add_node("validate", validate_data)
    .add_node("process", process_data)
    .add_edge(START, "fetch")
    .add_edge("fetch", "validate")
    .add_edge("validate", "process")
    .add_edge("process", END)
    .compile(checkpointer=checkpointer)
)

# === 步驟 1：執行圖 ===
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke({}, config)
print(f"執行結果: {result}")

# === 步驟 2：檢查歷史以除錯 ===
print("\n=== 歷史檢查 ===")
history = list(graph.get_state_history(config))
for state in history:
    print(f"  step={state.metadata['step']}, "
          f"next={state.next}, "
          f"values={state.values}")

# === 步驟 3：假設我們發現 validate 應該回傳不同結果 ===
# 找到 process 之前的 checkpoint
before_process = next(s for s in history if s.next == ("process",))
print(f"\nprocess 之前的 state: {before_process.values}")

# === 步驟 4：Fork 修正 state ===
# 假設我們想測試 validated=False 的情況
fork_config = graph.update_state(
    before_process.config,
    values={"validated": False},
)
fork_result = graph.invoke(None, fork_config)
print(f"修正後結果（validated=False）: {fork_result}")

# 也可以測試不同的 data
before_validate = next(s for s in history if s.next == ("validate",))
fork_config2 = graph.update_state(
    before_validate.config,
    values={"data": "invalid_data"},
)
fork_result2 = graph.invoke(None, fork_config2)
print(f"修正後結果（invalid data）: {fork_result2}")
