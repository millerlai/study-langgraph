# 3.2 範例：延遲執行（Deferred Nodes）
# 展示標記為 deferred=True 的節點在背景執行，不阻塞主流程。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import operator


# 1. 定義 State
class TaskState(TypedDict):
    input_data: str
    processed: str
    response: str
    logs: Annotated[list[str], operator.add]


# 2. 定義 Node 函數
def process_data(state: TaskState) -> dict:
    """主要處理邏輯"""
    processed = state["input_data"].upper()
    print(f"[process_data] 處理: '{state['input_data']}' -> '{processed}'")
    return {"processed": processed}


def log_activity(state: TaskState) -> dict:
    """背景日誌記錄（延遲節點）"""
    log_entry = f"已處理資料: '{state['input_data']}'"
    print(f"[log_activity] (背景) 記錄: {log_entry}")
    return {"logs": [log_entry]}


def generate_response(state: TaskState) -> dict:
    """產生回應"""
    response = f"處理完成: {state['processed']}"
    print(f"[generate_response] {response}")
    return {"response": response}


# 3. 建構 Graph
builder = StateGraph(TaskState)
builder.add_node("process_data", process_data)
builder.add_node("log_activity", log_activity, deferred=True)  # 延遲節點
builder.add_node("generate_response", generate_response)

builder.add_edge(START, "process_data")
builder.add_edge("process_data", "log_activity")
builder.add_edge("process_data", "generate_response")
builder.add_edge("generate_response", END)

graph = builder.compile()

# 4. 執行
result = graph.invoke({
    "input_data": "hello langgraph",
    "processed": "",
    "response": "",
    "logs": [],
})

print(f"\n回應: {result['response']}")
print(f"日誌: {result['logs']}")
