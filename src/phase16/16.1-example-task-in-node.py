# 16.1 範例：在 Node 中使用 @task
# 確保恢復時不重複執行已完成的副作用操作
# 需要：pip install langgraph requests

import uuid
from typing import NotRequired
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import task
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    urls: list[str]
    results: NotRequired[list[str]]


# === 將每個 API 呼叫包裝為 task ===
@task
def fetch_url(url: str) -> str:
    """
    每個 URL 的請求是獨立的 task
    恢復時，已成功的請求不會重新執行
    """
    import requests
    response = requests.get(url)
    return response.text[:200]  # 取前 200 字


@task
def summarize(text: str) -> str:
    """
    摘要也是獨立的 task
    即使這步失敗，之前的 fetch 不需要重做
    """
    # 實際應用中會呼叫 LLM
    return f"Summary of {len(text)} chars: {text[:50]}..."


def process_urls(state: State) -> dict:
    """
    Node 函數：協調多個 task 的執行
    """
    # 平行發起所有 URL 請求
    fetch_futures = [fetch_url(url) for url in state["urls"]]

    # 等待結果並進行摘要
    results = []
    for future in fetch_futures:
        text = future.result()          # 等待 fetch 完成
        summary = summarize(text)        # 發起摘要 task
        results.append(summary.result()) # 等待摘要完成

    return {"results": results}


# === 建構 Graph ===
builder = StateGraph(State)
builder.add_node("process_urls", process_urls)
builder.add_edge(START, "process_urls")
builder.add_edge("process_urls", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 執行 ===
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

result = graph.invoke(
    {"urls": ["https://www.example.com", "https://httpbin.org/get"]},
    config,
)
print(f"結果: {result['results']}")
