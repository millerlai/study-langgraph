# 11.1 範例：可注入參數 — 使用 previous 實現跨呼叫短期記憶
# 示範 @entrypoint 的 previous 參數注入

import uuid
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from typing import Any

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def accumulator(number: int, *, previous: Any = None) -> int:
    """累加器：每次呼叫把數字加上前一次的結果"""
    previous = previous or 0
    total = number + previous
    return total

config = {"configurable": {"thread_id": "acc-thread"}}

print(accumulator.invoke(1, config))   # 1  (previous=None → 0+1)
print(accumulator.invoke(2, config))   # 3  (previous=1 → 1+2)
print(accumulator.invoke(3, config))   # 6  (previous=3 → 3+3)
