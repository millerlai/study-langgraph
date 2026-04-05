# 11.1 範例：entrypoint.final — 分離回傳值與存儲值
# 示範回傳給呼叫者的值與存入 checkpoint 的值可以不同

import uuid
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def doubling_accumulator(n: int, *, previous: Any = None) -> entrypoint.final[int, int]:
    """
    回傳 previous 給呼叫者，但存儲 2*n 到 checkpoint。
    下次呼叫時 previous 會是 2*n。
    """
    previous = previous or 0
    # value=回傳值, save=存入checkpoint的值
    return entrypoint.final(value=previous, save=2 * n)

config = {"configurable": {"thread_id": "double-thread"}}

print(doubling_accumulator.invoke(3, config))  # 0   (previous=None)
print(doubling_accumulator.invoke(1, config))  # 6   (previous=2*3=6)
print(doubling_accumulator.invoke(5, config))  # 2   (previous=2*1=2)
