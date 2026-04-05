# 7.2 範例：多層 Namespace 組織記憶
# 展示如何設計階層式的記憶結構（全域、組織、使用者級別）

"""
多層 Namespace 組織記憶
展示如何設計階層式的記憶結構
"""
import uuid
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# ============================================================
# 1. 寫入不同層級的記憶
# ============================================================

# 全域設定
store.put(("global", "config"), "model-settings", {
    "default_model": "gpt-4o",
    "temperature": 0.7,
})

# 組織級別
store.put(("org-acme", "config"), "org-settings", {
    "plan": "enterprise",
    "max_tokens": 8000,
})

# 使用者級別 — 事實記憶
store.put(("org-acme", "user-001", "facts"), str(uuid.uuid4()), {
    "content": "使用者是後端工程師",
})
store.put(("org-acme", "user-001", "facts"), str(uuid.uuid4()), {
    "content": "使用者主要用 Python",
})

# 使用者級別 — 偏好記憶
store.put(("org-acme", "user-001", "prefs"), "style", {
    "response_style": "technical",
    "language": "zh-TW",
    "verbosity": "concise",
})

# 使用者級別 — 情節記憶
store.put(("org-acme", "user-001", "episodes"), str(uuid.uuid4()), {
    "event": "詢問了 FastAPI 部署方式",
    "date": "2025-12-01",
    "outcome": "成功部署到 AWS",
})

# ============================================================
# 2. 讀取不同層級
# ============================================================
print("=== 全域設定 ===")
config = store.get(("global", "config"), "model-settings")
print(f"  {config.value}")

print("\n=== 組織設定 ===")
org_config = store.get(("org-acme", "config"), "org-settings")
print(f"  {org_config.value}")

print("\n=== 使用者事實 ===")
facts = store.search(("org-acme", "user-001", "facts"))
for f in facts:
    print(f"  - {f.value['content']}")

print("\n=== 使用者偏好 ===")
prefs = store.get(("org-acme", "user-001", "prefs"), "style")
print(f"  {prefs.value}")

print("\n=== 使用者情節 ===")
episodes = store.search(("org-acme", "user-001", "episodes"))
for ep in episodes:
    print(f"  - [{ep.value['date']}] {ep.value['event']}")

# ============================================================
# 3. 建構完整的使用者上下文
# ============================================================
def build_user_context(store, org_id: str, user_id: str) -> str:
    """從多個 namespace 組合使用者上下文"""
    parts = []

    # 讀取事實
    facts = store.search((org_id, user_id, "facts"))
    if facts:
        fact_strs = [f.value["content"] for f in facts]
        parts.append(f"使用者資訊：{'; '.join(fact_strs)}")

    # 讀取偏好
    prefs_items = store.search((org_id, user_id, "prefs"))
    if prefs_items:
        for p in prefs_items:
            parts.append(f"偏好：{p.value}")

    # 讀取最近的情節
    episodes = store.search((org_id, user_id, "episodes"), limit=3)
    if episodes:
        ep_strs = [f"{e.value['event']}" for e in episodes]
        parts.append(f"最近互動：{'; '.join(ep_strs)}")

    return "\n".join(parts)

context = build_user_context(store, "org-acme", "user-001")
print("\n=== 組合後的使用者上下文 ===")
print(context)
