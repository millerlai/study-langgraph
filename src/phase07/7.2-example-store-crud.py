# 7.2 範例：InMemoryStore 基本 CRUD 操作
# 展示 put / get / search / delete 的用法

"""
InMemoryStore 基本 CRUD 操作
展示 put / get / search / delete 的用法
"""
import uuid
from langgraph.store.memory import InMemoryStore

# ============================================================
# 1. 建立 Store
# ============================================================
store = InMemoryStore()

# ============================================================
# 2. 寫入記憶 (PUT)
# ============================================================
user_id = "user-001"
namespace = (user_id, "memories")

# 寫入第一筆記憶
mem_id_1 = str(uuid.uuid4())
store.put(namespace, mem_id_1, {
    "type": "fact",
    "content": "使用者喜歡日本料理",
    "source": "對話推斷",
})

# 寫入第二筆記憶
mem_id_2 = str(uuid.uuid4())
store.put(namespace, mem_id_2, {
    "type": "fact",
    "content": "使用者住在台北市信義區",
    "source": "使用者提供",
})

# 寫入第三筆記憶
mem_id_3 = str(uuid.uuid4())
store.put(namespace, mem_id_3, {
    "type": "preference",
    "content": "偏好簡潔的回覆風格",
    "source": "行為分析",
})

print(f"已寫入 3 筆記憶到 namespace {namespace}")

# ============================================================
# 3. 讀取記憶 (GET)
# ============================================================
item = store.get(namespace, mem_id_1)
print(f"\n讀取單筆記憶:")
print(f"  key: {item.key}")
print(f"  value: {item.value}")
print(f"  created_at: {item.created_at}")

# ============================================================
# 4. 搜尋記憶 (SEARCH)
# ============================================================
all_memories = store.search(namespace)
print(f"\n搜尋所有記憶 (共 {len(all_memories)} 筆):")
for mem in all_memories:
    print(f"  [{mem.key[:8]}...] {mem.value['content']}")

# 使用 filter 過濾
facts_only = store.search(namespace, filter={"type": "fact"})
print(f"\n只搜尋 type=fact (共 {len(facts_only)} 筆):")
for mem in facts_only:
    print(f"  {mem.value['content']}")

# 限制回傳數量
limited = store.search(namespace, limit=2)
print(f"\n限制回傳 2 筆: {len(limited)} 筆")

# ============================================================
# 5. 更新記憶 (PUT with existing key)
# ============================================================
store.put(namespace, mem_id_1, {
    "type": "fact",
    "content": "使用者喜歡日本料理，尤其是壽司和拉麵",  # 更新
    "source": "對話推斷",
})

updated = store.get(namespace, mem_id_1)
print(f"\n更新後的記憶: {updated.value['content']}")

# ============================================================
# 6. 刪除記憶 (DELETE)
# ============================================================
store.delete(namespace, mem_id_3)
remaining = store.search(namespace)
print(f"\n刪除後剩餘 {len(remaining)} 筆記憶")

# ============================================================
# 7. 不同 Namespace 互不干擾
# ============================================================
other_namespace = ("user-002", "memories")
store.put(other_namespace, str(uuid.uuid4()), {
    "content": "user-002 的記憶"
})

user1_mems = store.search(namespace)
user2_mems = store.search(other_namespace)
print(f"\nuser-001 的記憶: {len(user1_mems)} 筆")
print(f"user-002 的記憶: {len(user2_mems)} 筆")
