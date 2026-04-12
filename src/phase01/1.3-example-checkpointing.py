# 1.3 第一個 Graph — 範例三：加入記憶（Checkpointing）
# 在 Tool Calling 基礎上加入 Checkpointer，支援多輪對話
# 需要設定 OPENAI_API_KEY 環境變數

"""
範例三：加入記憶（Checkpointing）
- 在範例二的基礎上加入 Checkpointer
- 支援多輪對話（記住之前說過的話）
- 使用 thread_id 區分不同的對話 session
- 示範跨輪次的上下文保持
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ

# ============================================================
# 1. 定義工具（同範例二）
# ============================================================
@tool
def get_weather(city: str) -> str:
    """查詢指定城市的天氣資訊。

    Args:
        city: 要查詢天氣的城市名稱
    """
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
        result = eval(expression)
        return f"計算結果：{expression} = {result}"
    except Exception as e:
        return f"計算錯誤：{e}"

tools = [get_weather, calculate]

# ============================================================
# 2. 初始化 LLM
# ============================================================
#model = ChatOpenAI(model="gpt-5-nano", temperature=0) # Set OPENAI_API_KEY in environment variables, you could create API key at https://platform.openai.com/settings/organization/api-keys

model = ChatAnthropic(model="claude-sonnet-4-5") # Set ANTHROPIC_API_KEY in environment variables , you could create API key at https://platform.claude.com/settings/keys
model_with_tools = model.bind_tools(tools)

# ============================================================
# 3. 定義 Nodes（同範例二）
# ============================================================
def chatbot(state: MessagesState) -> dict:
    """LLM 節點"""
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

# ============================================================
# 4. 建構 Graph（同範例二）
# ============================================================
builder = StateGraph(MessagesState)

builder.add_node("chatbot", chatbot)
builder.add_node("tools", tool_node)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

# ============================================================
# 5. 關鍵差異：使用 Checkpointer 編譯
# ============================================================
# InMemorySaver 將 State 保存在記憶體中（開發用）
# 正式環境可用 SqliteSaver 或 PostgresSaver
checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)
#                       ^^^^^^^^^^^^^^^^^^^^^^^^
#                       唯一的差異：加了 checkpointer！

# ============================================================
# 6. 多輪對話示範
# ============================================================

# thread_id 是對話的唯一識別碼
# 同一個 thread_id = 同一段對話，會保留上下文
config = {"configurable": {"thread_id": "conversation-001"}}

# --- 第一輪 ---
print("=== 第一輪 ===")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "你好！我叫小明。"}]},
    config,  # 傳入 config 指定 thread_id
)
print(f"AI: {result['messages'][-1].content}")

# --- 第二輪（AI 應該記得你叫小明）---
print("\n=== 第二輪 ===")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "你還記得我叫什麼名字嗎？"}]},
    config,  # 同一個 thread_id → 接續同一段對話
)
print(f"AI: {result['messages'][-1].content}")

# --- 第三輪（使用工具 + 記憶）---
print("\n=== 第三輪 ===")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "台北天氣如何？"}]},
    config,
)
print(f"AI: {result['messages'][-1].content}")

# --- 第四輪（AI 應該記得之前查過天氣）---
print("\n=== 第四輪 ===")
result = graph.invoke(
    {"messages": [{"role": "user", "content": "剛剛查到的溫度是幾度？"}]},
    config,
)
print(f"AI: {result['messages'][-1].content}")

# ============================================================
# 7. 不同的 thread_id = 全新的對話
# ============================================================
print("\n=== 全新對話（不同 thread_id） ===")
new_config = {"configurable": {"thread_id": "conversation-002"}}
result = graph.invoke(
    {"messages": [{"role": "user", "content": "你還記得我叫什麼嗎？"}]},
    new_config,  # 不同的 thread_id → 全新對話，沒有記憶
)
print(f"AI: {result['messages'][-1].content}")
# AI 不會記得「小明」，因為這是不同的 thread
