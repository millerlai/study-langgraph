# 7.2 範例：InMemoryStore 啟用語意搜尋
# 使用模擬的 embedding 函式展示語意搜尋功能
# 實際應用中可替換為 OpenAI 等 embedding 模型

"""
InMemoryStore 啟用語意搜尋
需要提供 embedding 函式（此範例使用模擬的 embedding）
"""
import uuid
from langgraph.store.memory import InMemoryStore

# ============================================================
# 1. 定義 Embedding 函式
# ============================================================

def mock_embed(texts: list[str]) -> list[list[float]]:
    """
    模擬 Embedding 函式
    實際應用中替換為：
      from langchain.embeddings import init_embeddings
      embed = init_embeddings("openai:text-embedding-3-small")
    """
    import hashlib
    results = []
    for text in texts:
        # 用 hash 模擬 embedding（僅供示範）
        h = hashlib.md5(text.encode()).hexdigest()
        vec = [int(h[i:i+2], 16) / 255.0 for i in range(0, 8, 2)]
        results.append(vec)
    return results

# ============================================================
# 2. 建立帶語意搜尋的 Store
# ============================================================
store = InMemoryStore(
    index={
        "embed": mock_embed,   # Embedding 函式
        "dims": 4,             # Embedding 維度（需與函式輸出匹配）
        "fields": ["content"], # 要 embed 的欄位（"$" 表示整個 value）
    }
)

# ============================================================
# 3. 寫入記憶
# ============================================================
user_ns = ("user-001", "memories")

memories = [
    {"content": "使用者喜歡吃壽司和拉麵等日本料理", "category": "food"},
    {"content": "使用者住在台北市信義區", "category": "location"},
    {"content": "使用者是軟體工程師，主要用 Python", "category": "work"},
    {"content": "使用者週末喜歡去爬山和攝影", "category": "hobby"},
    {"content": "使用者偏好暗色主題的 IDE", "category": "preference"},
    {"content": "使用者養了一隻名叫咪咪的貓", "category": "personal"},
]

for mem in memories:
    store.put(user_ns, str(uuid.uuid4()), mem)

print(f"已寫入 {len(memories)} 筆記憶")

# ============================================================
# 4. 語意搜尋
# ============================================================
print("\n--- 搜尋：飲食偏好 ---")
results = store.search(user_ns, query="使用者喜歡吃什麼食物？", limit=3)
for r in results:
    print(f"  [{r.value.get('category', '?')}] {r.value['content']}")

print("\n--- 搜尋：住在哪裡 ---")
results = store.search(user_ns, query="使用者住在哪個城市？", limit=3)
for r in results:
    print(f"  [{r.value.get('category', '?')}] {r.value['content']}")

print("\n--- 搜尋：工作與技術 ---")
results = store.search(user_ns, query="使用者的職業和技術棧是什麼？", limit=3)
for r in results:
    print(f"  [{r.value.get('category', '?')}] {r.value['content']}")

# ============================================================
# 5. 結合 filter 和語意搜尋
# ============================================================
print("\n--- 結合 filter：只搜尋 category=food ---")
results = store.search(
    user_ns,
    query="使用者的喜好",
    filter={"category": "food"},
    limit=3,
)
for r in results:
    print(f"  [{r.value.get('category', '?')}] {r.value['content']}")

# ============================================================
# 6. 控制哪些欄位被 embed
# ============================================================

# 只 embed 特定欄位
store.put(
    user_ns,
    str(uuid.uuid4()),
    {
        "content": "使用者最近開始學習 Rust 語言",
        "metadata": "2025-12-15 的對話中提及",
        "category": "learning",
    },
    index=["content"],  # 只對 content 欄位做 embedding
)

# 完全不做 embedding（仍可用 filter 搜尋，但語意搜尋找不到）
store.put(
    user_ns,
    "internal-note",
    {"content": "內部系統備註：需要驗證使用者身分", "internal": True},
    index=False,  # 不做 embedding
)

print("\n--- 搜尋不會找到 index=False 的記憶 ---")
results = store.search(user_ns, query="系統備註", limit=5)
print(f"  找到 {len(results)} 筆結果")
