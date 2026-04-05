# 11.1 範例：並行執行多個 Task — 提升 I/O 密集型任務的效能
# 示範同時啟動多個 task 並行執行

import uuid
import time
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

@task
def fetch_data(source: str) -> dict:
    """模擬從不同來源抓取資料"""
    time.sleep(0.5)  # 模擬 I/O 延遲
    data_map = {
        "news": {"title": "AI 突破", "category": "科技"},
        "weather": {"city": "台北", "temp": 28},
        "stocks": {"index": "TAIEX", "value": 22000},
    }
    return data_map.get(source, {"error": "未知來源"})

@task
def merge_results(results: list[dict]) -> str:
    """合併所有資料來源的結果"""
    return " | ".join(str(r) for r in results)

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def data_pipeline(sources: list[str]) -> str:
    """平行抓取多個資料來源，然後合併"""
    # 同時啟動所有 task（不等待）
    futures = [fetch_data(src) for src in sources]
    # 一次收集所有結果
    results = [f.result() for f in futures]
    return merge_results(results).result()

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

start = time.time()
result = data_pipeline.invoke(["news", "weather", "stocks"], config=config)
elapsed = time.time() - start

print(f"結果: {result}")
print(f"耗時: {elapsed:.2f}s （三個 0.5s task 並行執行）")
# 結果: {'title': 'AI 突破', 'category': '科技'} | {'city': '台北', 'temp': 28} | {'index': 'TAIEX', 'value': 22000}
# 耗時: ~0.5s（而非 1.5s）
