# 16.3 範例：EncryptedSerializer 概念展示
# 展示加密序列化的基本概念（使用模擬實作）
# 真實使用需要：pip install pycryptodome langgraph-checkpoint-sqlite
# 真實使用需要：設定 LANGGRAPH_AES_KEY 環境變數

import os

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# 設定 AES key（32 bytes = 256 bit，base64 編碼）
# 在真實環境中，這應該從環境變數或密鑰管理系統取得
# os.environ["LANGGRAPH_AES_KEY"] = "your-32-byte-base64-encoded-key"

# === 展示概念（不需要真實 key） ===
print("=== EncryptedSerializer 概念展示 ===\n")

# 模擬加密流程
class MockEncryptedSerializer:
    """模擬 EncryptedSerializer 的行為"""

    def __init__(self, inner_serde, key: bytes):
        self.inner = inner_serde
        self.key = key

    def dumps(self, obj) -> bytes:
        # 1. 先用內部序列化器序列化
        plain_bytes = self.inner.dumps(obj)
        # 2. 加密（此處模擬，真實使用 AES-GCM）
        encrypted = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(plain_bytes)])
        return encrypted

    def loads(self, data: bytes):
        # 1. 解密
        decrypted = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(data)])
        # 2. 反序列化
        return self.inner.loads(decrypted)


inner = JsonPlusSerializer()
mock_key = b"0123456789abcdef"  # 模擬 key

mock_encrypted = MockEncryptedSerializer(inner, mock_key)

# 測試
test_data = {"user_id": "alice", "secret": "my-api-key-12345"}
encrypted = mock_encrypted.dumps(test_data)
decrypted = mock_encrypted.loads(encrypted)

print(f"原始資料: {test_data}")
print(f"加密後 (前 20 bytes): {encrypted[:20]}...")
print(f"解密後: {decrypted}")
print(f"加密前後一致: {test_data == decrypted}")
