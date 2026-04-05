# 7.1 範例：使用 langchain_core 的 trim_messages 工具
# 按 token 數量自動裁剪訊息（適合精確控制 token 使用量）

"""
使用 langchain_core 的 trim_messages 工具
按 token 數量自動裁剪（適合精確控制 token 使用量）
"""
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, trim_messages
)

# 模擬一段長對話
messages = [
    SystemMessage(content="你是一個 Python 專家。"),
    HumanMessage(content="什麼是 list comprehension？"),
    AIMessage(content="List comprehension 是 Python 的一種簡潔語法..."),
    HumanMessage(content="給我一個範例"),
    AIMessage(content="例如 [x**2 for x in range(10)]..."),
    HumanMessage(content="怎麼加條件過濾？"),
    AIMessage(content="在後面加 if 條件即可..."),
    HumanMessage(content="巢狀的呢？"),
]

# 策略一：保留最後 N 條訊息
trimmed = trim_messages(
    messages,
    max_tokens=100,            # 最多 100 token
    strategy="last",           # 從尾端保留
    token_counter=len,         # 簡化：用字元數代替 token 計數
    include_system=True,       # 始終保留系統訊息
    allow_partial=False,       # 不拆分單一訊息
)

print("裁剪後的訊息:")
for msg in trimmed:
    print(f"  [{msg.type}] {msg.content[:40]}...")
