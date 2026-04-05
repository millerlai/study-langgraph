# 1.3 第一個 Graph — 範例二：加入工具（Tool Calling）
# LLM + 工具呼叫，形成 ReAct 迴圈
# 需要設定 OPENAI_API_KEY 環境變數

"""
範例二：加入工具（Tool Calling）
- LLM 可以決定是否呼叫工具
- 使用 ToolNode 自動執行工具
- 使用 tools_condition 條件路由
- 形成 ReAct 迴圈：llm → tool → llm → ... → END
"""
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# ============================================================
# 1. 定義工具
# ============================================================
@tool
def get_weather(city: str) -> str:
    """查詢指定城市的天氣資訊。

    Args:
        city: 要查詢天氣的城市名稱
    """
    # 模擬天氣 API（實際應用中會呼叫真正的 API）
    weather_data = {
        "台北": "☀️ 晴天，28°C，濕度 65%",
        "東京": "🌤️ 多雲，22°C，濕度 55%",
        "紐約": "🌧️ 小雨，15°C，濕度 80%",
    }
    return weather_data.get(city, f"抱歉，找不到 {city} 的天氣資料")

@tool
def calculate(expression: str) -> str:
    """計算數學運算式。

    Args:
        expression: 要計算的數學運算式，例如 "2 + 3 * 4"
    """
    try:
        result = eval(expression)  # 注意：正式環境請用安全的計算方式
        return f"計算結果：{expression} = {result}"
    except Exception as e:
        return f"計算錯誤：{e}"

# 工具列表
tools = [get_weather, calculate]

# ============================================================
# 2. 初始化 LLM 並綁定工具
# ============================================================
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# bind_tools 讓 LLM 知道有哪些工具可用
# LLM 會在適當時機自動決定是否呼叫工具
model_with_tools = model.bind_tools(tools)

# ============================================================
# 3. 定義 Nodes
# ============================================================
def chatbot(state: MessagesState) -> dict:
    """
    LLM 節點：
    - 使用綁定了工具的 model
    - LLM 可能回傳純文字回應（不需要工具）
    - 也可能回傳 tool_calls（需要呼叫工具）
    """
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# ToolNode 是 LangGraph 的預建節點
# 它會自動：
#   1. 讀取最後一則 AIMessage 中的 tool_calls
#   2. 執行對應的工具函數
#   3. 將結果包裝成 ToolMessage 回傳
tool_node = ToolNode(tools)

# ============================================================
# 4. 建構 Graph
# ============================================================
builder = StateGraph(MessagesState)

# 註冊節點
builder.add_node("chatbot", chatbot)
builder.add_node("tools", tool_node)

# 定義邊
builder.add_edge(START, "chatbot")

# 條件邊：chatbot 完成後，檢查是否有 tool_calls
# tools_condition 是 LangGraph 預建的路由函數：
#   - 如果 AIMessage 有 tool_calls → 導向 "tools" 節點
#   - 如果沒有 tool_calls → 導向 END
builder.add_conditional_edges("chatbot", tools_condition)

# 工具執行完後 → 回到 chatbot（讓 LLM 看到工具結果）
builder.add_edge("tools", "chatbot")

# 編譯
graph = builder.compile()

# ============================================================
# 5. 執行——不需要工具的情況
# ============================================================
print("=== 測試一：不需要工具 ===")
result = graph.invoke({
    "messages": [{"role": "user", "content": "你好！你是誰？"}]
})
print(result["messages"][-1].content)

# ============================================================
# 6. 執行——需要工具的情況
# ============================================================
print("\n=== 測試二：查天氣（需要工具） ===")
result = graph.invoke({
    "messages": [{"role": "user", "content": "台北現在天氣如何？"}]
})
print(result["messages"][-1].content)

# ============================================================
# 7. 執行——需要多個工具的情況
# ============================================================
print("\n=== 測試三：複合問題（可能用多個工具） ===")
result = graph.invoke({
    "messages": [{"role": "user", "content": "台北和東京的溫度差幾度？請幫我算一下。"}]
})
print(result["messages"][-1].content)
