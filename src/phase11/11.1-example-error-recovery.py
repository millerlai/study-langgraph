# 11.1 範例：錯誤恢復 — task 結果已存入 checkpoint，恢復時不需重新執行
# 示範 checkpoint 的錯誤恢復機制

import time
import uuid
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

attempt_count = 0

@task
def slow_task() -> str:
    """耗時任務"""
    time.sleep(1)
    return "慢速任務完成"

@task
def flaky_task() -> str:
    """不穩定任務：第一次會失敗"""
    global attempt_count
    attempt_count += 1
    if attempt_count < 2:
        raise ValueError("模擬失敗")
    return "不穩定任務成功"

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def pipeline(inputs: dict) -> str:
    slow_result = slow_task().result()    # 結果會存入 checkpoint
    flaky_result = flaky_task().result()  # 第一次執行時這裡會拋錯
    return f"{slow_result} + {flaky_result}"

config = {"configurable": {"thread_id": "error-recovery"}}

# 第一次呼叫：slow_task 成功，flaky_task 失敗
try:
    pipeline.invoke({"run": 1}, config=config)
except ValueError:
    print("第一次執行失敗（預期中）")

# 恢復執行：slow_task 從 checkpoint 取回（不重新執行），flaky_task 重試成功
result = pipeline.invoke(None, config=config)
print(f"恢復後結果: {result}")
# 輸出:
# 第一次執行失敗（預期中）
# 恢復後結果: 慢速任務完成 + 不穩定任務成功
