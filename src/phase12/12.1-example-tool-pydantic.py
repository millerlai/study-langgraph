# 12.1 範例：進階 Schema 定義 — 使用 Pydantic 定義複雜的工具輸入
# 示範以 Pydantic BaseModel 定義 args_schema

from pydantic import BaseModel, Field
from typing import Literal
from langchain.tools import tool

# ============================================================
# 1. 使用 Pydantic 定義輸入 Schema
# ============================================================
class WeatherInput(BaseModel):
    """天氣查詢的輸入參數"""
    location: str = Field(description="城市名稱或座標")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="溫度單位偏好"
    )
    include_forecast: bool = Field(
        default=False,
        description="是否包含 5 天預報"
    )

@tool(args_schema=WeatherInput)
def get_weather(
    location: str,
    units: str = "celsius",
    include_forecast: bool = False
) -> str:
    """取得目前天氣和可選的預報。"""
    temp = 28 if units == "celsius" else 82
    result = f"{location} 目前天氣: {temp}°{'C' if units == 'celsius' else 'F'}"
    if include_forecast:
        result += "\n未來 5 天: 晴天為主"
    return result

# 測試工具
print(get_weather.invoke({
    "location": "台北",
    "units": "celsius",
    "include_forecast": True
}))
# 輸出:
# 台北 目前天氣: 28°C
# 未來 5 天: 晴天為主
