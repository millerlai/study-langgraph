# 16.3 範例：pickle_fallback 處理不支援的類型
# 需要：pip install langgraph
# 注意：pickle_fallback 有安全風險，僅在開發環境使用

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


# === 不用 pickle_fallback（預設） ===
serde_strict = JsonPlusSerializer()

# 一般 dict 可以正常序列化
normal_data = {"key": "value", "numbers": [1, 2, 3]}
serialized = serde_strict.dumps(normal_data)
deserialized = serde_strict.loads(serialized)
print(f"一般資料: {deserialized}")


# === 使用 pickle_fallback ===
serde_pickle = JsonPlusSerializer(pickle_fallback=True)

# 自定義 class 需要 pickle
class CustomObject:
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __repr__(self):
        return f"CustomObject(name={self.name!r}, data={self.data!r})"


custom = CustomObject("test", [1, 2, 3])
serialized = serde_pickle.dumps(custom)
deserialized = serde_pickle.loads(serialized)
print(f"自定義物件: {deserialized}")


# === 在 Checkpointer 中使用 ===
checkpointer_with_pickle = InMemorySaver(
    serde=JsonPlusSerializer(pickle_fallback=True)
)
print(f"\n已建立 pickle_fallback checkpointer: {checkpointer_with_pickle}")
print("提醒：pickle_fallback 有安全風險，僅在開發環境使用")
