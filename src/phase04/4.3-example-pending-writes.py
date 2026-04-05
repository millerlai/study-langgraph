# 4.3 範例：Pending Writes（失敗時的寫入保留）
# 展示平行節點部分失敗時，已成功節點的寫入會被保留，恢復時不需重新執行。

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
from operator import add

# === 1. 定義 State ===
class State(TypedDict):
    results: Annotated[list[str], add]

# === 2. 用全域變數模擬失敗 ===
call_count = 0

def reliable_node(state: State) -> dict:
    """總是成功的節點"""
    return {"results": ["reliable 完成"]}

def flaky_node(state: State) -> dict:
    """第一次呼叫時失敗，第二次成功"""
    global call_count
    call_count += 1
    if call_count == 1:
        raise RuntimeError("暫時性錯誤！")
    return {"results": ["flaky 完成"]}

# === 3. 建構圖——兩個節點平行執行 ===
builder = StateGraph(State)
builder.add_node("reliable", reliable_node)
builder.add_node("flaky", flaky_node)

# 兩個節點都從 START 出發（平行）
builder.add_edge(START, "reliable")
builder.add_edge(START, "flaky")
builder.add_edge("reliable", END)
builder.add_edge("flaky", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 4. 第一次執行——flaky_node 會失敗 ===
config = {"configurable": {"thread_id": "pending_demo"}}
try:
    result = graph.invoke({"results": ["開始"]}, config)
except Exception as e:
    print(f"執行失敗: {e}")
    # 執行失敗: 暫時性錯誤！

# === 5. 查看 State——reliable_node 的結果已被保留 ===
state = graph.get_state(config)
print(f"目前 values: {state.values}")
print(f"下一步: {state.next}")
# 目前 values: {'results': ['開始']}
# 下一步: ('reliable', 'flaky')

# === 6. 恢復執行——reliable_node 不會重新執行 ===
# call_count 已經是 1，第二次呼叫 flaky_node 會成功
result = graph.invoke(None, config)
print(f"恢復後結果: {result['results']}")
# 恢復後結果: ['開始', 'reliable 完成', 'flaky 完成']
# reliable_node 的 pending write 被使用，不需重新執行
