# 12.2 範例：建立使用 HTTP 傳輸的 MCP Server（天氣查詢工具）
# 需要安裝：pip install fastmcp
# 啟動方式：python 12.2-example-mcp-weather-server.py

from fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """查詢指定地點的天氣。

    Args:
        location: 城市名稱
    """
    # 模擬天氣資料
    weather_data = {
        "台北": "晴天，28°C，濕度 65%",
        "東京": "多雲，22°C，濕度 55%",
        "紐約": "雨天，15°C，濕度 80%",
    }
    return weather_data.get(location, f"{location} 的天氣資料暫時無法取得")

@mcp.tool()
async def get_forecast(location: str, days: int = 3) -> str:
    """查詢未來幾天的天氣預報。

    Args:
        location: 城市名稱
        days: 預報天數（1-7 天）
    """
    if days < 1 or days > 7:
        return "預報天數必須在 1-7 天之間"
    return f"{location} 未來 {days} 天預報: 晴時多雲，氣溫 25-30°C"

if __name__ == "__main__":
    # 使用 HTTP 傳輸，適合遠端部署
    mcp.run(transport="streamable-http")

print("MCP Weather Server 定義完成")
print("工具: get_weather, get_forecast")
print("啟動方式: python 12.2-example-mcp-weather-server.py")
