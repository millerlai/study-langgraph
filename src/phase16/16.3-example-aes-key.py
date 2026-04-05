# 16.3 範例：AES Key 產生與管理
# 展示如何安全地產生和使用加密金鑰
# 需要：Python 標準庫（無額外依賴）

import base64
import os


# === 方法 1：用 Python 產生隨機 key ===
def generate_aes_key() -> str:
    """產生 32 bytes (256 bit) 的 AES key，回傳 base64 編碼字串"""
    random_bytes = os.urandom(32)
    return base64.b64encode(random_bytes).decode("utf-8")


key = generate_aes_key()
print(f"產生的 AES key: {key}")
print(f"key 長度: {len(base64.b64decode(key))} bytes (256 bit)")

# === 方法 2：驗證 key 格式 ===
def validate_aes_key(key_str: str) -> bool:
    """驗證 AES key 是否為有效的 base64 編碼 32 bytes"""
    try:
        decoded = base64.b64decode(key_str)
        return len(decoded) == 32
    except Exception:
        return False


print(f"\nkey 驗證: {validate_aes_key(key)}")
print(f"無效 key 驗證: {validate_aes_key('too-short')}")

# === 方法 3：設定環境變數 ===
print("\n=== 環境變數設定方式 ===")
print()
print("Linux / macOS:")
print(f"  export LANGGRAPH_AES_KEY='{key}'")
print()
print("Windows (PowerShell):")
print(f"  $env:LANGGRAPH_AES_KEY='{key}'")
print()
print(".env 檔案:")
print(f"  LANGGRAPH_AES_KEY={key}")
print()
print("Docker:")
print(f"  docker run -e LANGGRAPH_AES_KEY='{key}' ...")

# === 方法 4：在程式碼中讀取（用於 from_pycryptodome_aes） ===
print("\n=== 程式碼中的用法 ===")
print()
print("# 自動從環境變數讀取")
print("serde = EncryptedSerializer.from_pycryptodome_aes()")
print()
print("# 手動傳入 key")
print(f"serde = EncryptedSerializer.from_pycryptodome_aes(key='{key}')")
