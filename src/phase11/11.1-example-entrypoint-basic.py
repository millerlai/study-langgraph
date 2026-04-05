# 11.1 範例：@entrypoint 基本用法 — 建立簡單的數字分類工作流
# 示範 @entrypoint 與 @task 的基本搭配使用

import uuid
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 1. 定義 Task
# ============================================================
@task
def is_even(number: int) -> bool:
    """檢查數字是否為偶數"""
    return number % 2 == 0

@task
def format_message(even: bool) -> str:
    """根據結果格式化訊息"""
    return "這是偶數" if even else "這是奇數"

# ============================================================
# 2. 定義 Entrypoint
# ============================================================
checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def classify_number(inputs: dict) -> str:
    """數字分類工作流"""
    even = is_even(inputs["number"]).result()
    return format_message(even).result()

# ============================================================
# 3. 執行工作流
# ============================================================
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = classify_number.invoke({"number": 7}, config=config)
print(result)
# 輸出: 這是奇數

result2 = classify_number.invoke({"number": 42}, config=config)
print(result2)
# 輸出: 這是偶數
