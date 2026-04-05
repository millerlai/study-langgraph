# 16.3 範例：JsonPlusSerializer 基本用法
# 展示預設序列化器如何處理各種類型
# 需要：pip install langgraph

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

serde = JsonPlusSerializer()

# === 測試各種類型的序列化 ===
import datetime
import uuid
from enum import Enum


class Priority(Enum):
    LOW = "low"
    HIGH = "high"


test_data = {
    "string": "Hello 你好",
    "number": 42,
    "float": 3.14,
    "boolean": True,
    "none": None,
    "datetime": datetime.datetime(2025, 1, 1, 12, 0, 0),
    "uuid": uuid.UUID("12345678-1234-5678-1234-567812345678"),
    "enum": Priority.HIGH,
    "bytes": b"binary data",
    "nested": {
        "list": [1, 2, 3],
        "set_data": {4, 5, 6},  # set 會被特殊處理
    },
}

# 序列化
serialized = serde.dumps(test_data)
print(f"序列化後類型: {type(serialized)}")
print(f"序列化後大小: {len(serialized)} bytes")

# 反序列化
deserialized = serde.loads(serialized)
print(f"\n反序列化結果:")
for key, value in deserialized.items():
    print(f"  {key}: {value!r} (type={type(value).__name__})")
