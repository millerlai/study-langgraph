# 6.1 範例：custom 模式 - 使用 get_stream_writer() 自定義串流資料
# 展示在節點中用 stream_writer 回報進度更新等自定義資訊
"""
custom 模式：使用 get_stream_writer() 自定義串流資料
適合串流進度更新、狀態訊息等自定義資訊
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer
import time

class State(TypedDict):
    query: str
    result: str

def search_and_process(state: State) -> dict:
    """模擬耗時的搜尋和處理過程，用 stream_writer 回報進度"""
    writer = get_stream_writer()

    # 階段 1：搜尋
    writer({"status": "searching", "progress": 0.0, "message": "正在搜尋..."})
    time.sleep(0.1)  # 模擬耗時操作

    writer({"status": "searching", "progress": 0.3, "message": "找到 5 筆結果"})
    time.sleep(0.1)

    # 階段 2：分析
    writer({"status": "analyzing", "progress": 0.6, "message": "正在分析結果..."})
    time.sleep(0.1)

    # 階段 3：生成
    writer({"status": "generating", "progress": 0.9, "message": "正在生成摘要..."})
    time.sleep(0.1)

    writer({"status": "done", "progress": 1.0, "message": "完成！"})

    return {"result": f"關於「{state['query']}」的搜尋摘要"}

builder = StateGraph(State)
builder.add_node("search_and_process", search_and_process)
builder.add_edge(START, "search_and_process")
builder.add_edge("search_and_process", END)
graph = builder.compile()

# ============================================================
# 使用 custom 模式接收自定義串流資料
# ============================================================
print("=== custom 模式 ===")
for chunk in graph.stream(
    {"query": "LangGraph streaming", "result": ""},
    stream_mode="custom",
    version="v2",
):
    data = chunk["data"]
    print(f"  [{data['status']}] {data['progress']*100:.0f}% - {data['message']}")

# [searching] 0% - 正在搜尋...
# [searching] 30% - 找到 5 筆結果
# [analyzing] 60% - 正在分析結果...
# [generating] 90% - 正在生成摘要...
# [done] 100% - 完成！
