# 12.1 範例：基本工具定義 — 使用 @tool 裝飾器
# 示範最簡單的工具定義方式，包含自訂名稱與描述

from langchain.tools import tool

# ============================================================
# 1. 最簡單的工具
# ============================================================
@tool
def search_database(query: str, limit: int = 10) -> str:
    """搜尋客戶資料庫，找出符合條件的記錄。

    Args:
        query: 搜尋關鍵字
        limit: 最多回傳幾筆結果
    """
    # 模擬資料庫搜尋
    return f"找到 {limit} 筆關於 '{query}' 的結果"

# ============================================================
# 2. 自訂工具名稱
# ============================================================
@tool("web_search")
def search(query: str) -> str:
    """在網路上搜尋資訊。"""
    return f"搜尋結果: {query}"

print(f"工具名稱: {search.name}")  # web_search

# ============================================================
# 3. 自訂名稱與描述
# ============================================================
@tool("calculator", description="執行數學計算。遇到數學問題時使用此工具。")
def calc(expression: str) -> str:
    """計算數學表達式。"""
    return str(eval(expression))

print(f"工具名稱: {calc.name}")           # calculator
print(f"工具描述: {calc.description}")     # 執行數學計算。遇到數學問題時使用此工具。
