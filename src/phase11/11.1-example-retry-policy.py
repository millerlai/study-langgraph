# 11.1 範例：RetryPolicy — 自動重試失敗的 task
# 示範設定重試策略，遇到特定例外時自動重試

import uuid
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import InMemorySaver

# 模擬不穩定的 API
call_count = 0

# 設定重試策略：遇到 ValueError 時重試
retry_policy = RetryPolicy(retry_on=ValueError)

@task(retry_policy=retry_policy)
def unstable_api_call() -> str:
    """模擬一個會失敗一次的 API 呼叫"""
    global call_count
    call_count += 1
    if call_count < 2:
        raise ValueError("暫時性失敗：API 回應超時")
    return "API 回應成功：資料已取得"

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def workflow(inputs: dict) -> str:
    return unstable_api_call().result()

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = workflow.invoke({"query": "test"}, config=config)
print(result)
# 輸出: API 回應成功：資料已取得
# （第一次呼叫失敗，自動重試後成功）
