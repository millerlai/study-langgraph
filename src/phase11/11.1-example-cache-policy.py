# 11.1 範例：CachePolicy — 快取 task 結果，設定 TTL
# 示範使用快取避免重複執行耗時計算

import time
from langgraph.func import entrypoint, task
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache

@task(cache_policy=CachePolicy(ttl=120))  # 快取 120 秒
def expensive_computation(x: int) -> int:
    """模擬耗時計算"""
    time.sleep(1)  # 模擬長時間運算
    return x * 2

@entrypoint(cache=InMemoryCache())
def workflow(inputs: dict) -> dict:
    # 第一次呼叫：實際執行（耗時 1 秒）
    result1 = expensive_computation(inputs["x"]).result()
    # 第二次呼叫：從快取取得（幾乎瞬間）
    result2 = expensive_computation(inputs["x"]).result()
    return {"result1": result1, "result2": result2}

start = time.time()
for chunk in workflow.stream({"x": 5}, stream_mode="updates"):
    print(chunk)
elapsed = time.time() - start

print(f"\n耗時: {elapsed:.2f}s （第二次呼叫從快取取得）")
# 輸出:
# {'expensive_computation': 10}
# {'expensive_computation': 10, '__metadata__': {'cached': True}}
# {'workflow': {'result1': 10, 'result2': 10}}
# 耗時: ~1.0s（而非 2.0s）
