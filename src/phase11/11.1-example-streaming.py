# 11.1 範例：Functional API 的串流支援
# 示範使用 get_stream_writer 自訂串流輸出

import uuid
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer

@task
def step_a(x: int) -> int:
    return x + 1

@task
def step_b(x: int) -> int:
    return x + 2

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def streaming_workflow(inputs: dict) -> int:
    writer = get_stream_writer()
    writer("開始處理...")

    a = step_a(inputs["x"]).result()
    writer(f"步驟 A 完成，結果: {a}")

    b = step_b(a).result()
    writer(f"步驟 B 完成，結果: {b}")

    return b

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

for mode, chunk in streaming_workflow.stream(
    {"x": 5},
    stream_mode=["custom", "updates"],
    config=config
):
    print(f"[{mode}] {chunk}")
# 輸出:
# [custom] 開始處理...
# [updates] {'step_a': 6}
# [custom] 步驟 A 完成，結果: 6
# [updates] {'step_b': 8}
# [custom] 步驟 B 完成，結果: 8
# [updates] {'streaming_workflow': 8}
