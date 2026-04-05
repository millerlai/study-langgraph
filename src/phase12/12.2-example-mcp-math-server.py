# 12.2 範例：建立一個簡單的 MCP Server（數學計算工具）
# 需要安裝：pip install fastmcp
# 啟動方式：python 12.2-example-mcp-math-server.py

from fastmcp import FastMCP

# ============================================================
# 1. 建立 MCP Server 實例
# ============================================================
mcp = FastMCP("Math")

# ============================================================
# 2. 定義工具
# ============================================================
@mcp.tool()
def add(a: int, b: int) -> int:
    """兩個數字相加。

    Args:
        a: 第一個數字
        b: 第二個數字
    """
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """兩個數字相乘。

    Args:
        a: 第一個數字
        b: 第二個數字
    """
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """除法計算。

    Args:
        a: 被除數
        b: 除數（不可為零）
    """
    if b == 0:
        raise ValueError("除數不能為零")
    return a / b

# ============================================================
# 3. 啟動 Server（使用 stdio 傳輸）
# ============================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")
    # 也可以用 HTTP 傳輸：
    # mcp.run(transport="streamable-http")

print("MCP Math Server 定義完成")
print("工具: add, multiply, divide")
print("啟動方式: python 12.2-example-mcp-math-server.py")
