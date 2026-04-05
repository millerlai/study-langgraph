# 2.3 Private State — 基本用法：節點之間的私有資料傳遞
# 展示如何在節點之間傳遞不屬於主 State 的私有資料
# 不需要 API key

"""
Private State 基本用法
展示如何在節點之間傳遞不屬於主 State 的私有資料
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 Schema
# ============================================================

# 主 State（公開的，外部看得到）
class OverallState(TypedDict):
    a: str

# Node 1 的輸出 Schema（包含私有欄位）
class Node1Output(TypedDict):
    private_data: str      # 這個欄位不在 OverallState 中 → 私有

# Node 2 的輸入 Schema（讀取私有欄位）
class Node2Input(TypedDict):
    private_data: str      # 從 Node 1 的輸出讀取

# ============================================================
# 2. 定義 Nodes
# ============================================================

def node_1(state: OverallState) -> Node1Output:
    """
    讀取 OverallState，寫入 private_data
    private_data 不在 OverallState 中，所以是「私有」的
    """
    output = {"private_data": "set by node_1"}
    print(f"node_1 輸入: {state}")
    print(f"node_1 輸出: {output}")
    return output

def node_2(state: Node2Input) -> OverallState:
    """
    讀取 private_data（私有），寫入 OverallState（公開）
    """
    output = {"a": f"processed: {state['private_data']}"}
    print(f"node_2 輸入: {state}")
    print(f"node_2 輸出: {output}")
    return output

def node_3(state: OverallState) -> OverallState:
    """
    只能讀取 OverallState，看不到 private_data
    """
    output = {"a": f"final: {state['a']}"}
    print(f"node_3 輸入: {state}")
    print(f"node_3 輸出: {output}")
    return output

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(OverallState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({"a": "initial"})

# 執行輸出：
# node_1 輸入: {'a': 'initial'}
# node_1 輸出: {'private_data': 'set by node_1'}
# node_2 輸入: {'private_data': 'set by node_1'}
# node_2 輸出: {'a': 'processed: set by node_1'}
# node_3 輸入: {'a': 'processed: set by node_1'}   ← 看不到 private_data！
# node_3 輸出: {'a': 'final: processed: set by node_1'}

print(result)
# {'a': 'final: processed: set by node_1'}
# ← 最終輸出也看不到 private_data
