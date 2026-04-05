# 13.3 範例：SQL 查詢安全驗證工具
# 在執行查詢前進行多重安全檢查
# 此範例不需要 API key，可直接執行

import re
from typing import TypedDict


# 危險關鍵字黑名單
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER",
    "CREATE", "TRUNCATE", "EXEC", "EXECUTE",
    "GRANT", "REVOKE", "--", ";--", "/*",
]


class QueryValidationResult(TypedDict):
    is_safe: bool
    query: str
    warnings: list[str]


def validate_sql_query(query: str) -> QueryValidationResult:
    """
    驗證 SQL 查詢的安全性

    檢查項目：
    1. 是否包含危險關鍵字（DML/DDL）
    2. 是否包含多條語句（SQL 注入）
    3. 是否有合理的 LIMIT
    """
    warnings = []
    query_upper = query.upper().strip()

    # 檢查 1：危險關鍵字
    for keyword in DANGEROUS_KEYWORDS:
        # 使用 word boundary 避免誤判
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_upper):
            warnings.append(f"包含危險關鍵字：{keyword}")

    # 檢查 2：多條語句（排除字串中的分號）
    # 簡易檢查：去掉字串後看是否有多個分號
    cleaned = re.sub(r"'[^']*'", "", query)
    if cleaned.count(";") > 1:
        warnings.append("包含多條 SQL 語句，可能是 SQL 注入")

    # 檢查 3：是否以 SELECT 開頭
    if not query_upper.startswith("SELECT"):
        warnings.append("查詢不是以 SELECT 開頭")

    # 檢查 4：是否有 LIMIT
    if "LIMIT" not in query_upper:
        warnings.append("查詢沒有 LIMIT 限制，建議加上")

    is_safe = len([w for w in warnings if "危險" in w or "注入" in w]) == 0

    return {
        "is_safe": is_safe,
        "query": query,
        "warnings": warnings,
    }


# ---- 測試驗證 ----
if __name__ == "__main__":
    test_queries = [
        "SELECT Name FROM Artist LIMIT 5",
        "SELECT * FROM Artist; DROP TABLE Artist;",
        "DELETE FROM Artist WHERE ArtistId = 1",
        "SELECT Name, COUNT(*) FROM Album GROUP BY ArtistId",
    ]

    for q in test_queries:
        result = validate_sql_query(q)
        status = "SAFE" if result["is_safe"] else "DANGEROUS"
        print(f"[{status}] {q}")
        for w in result["warnings"]:
            print(f"  Warning: {w}")
        print()
