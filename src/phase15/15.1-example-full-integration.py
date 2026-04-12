# 15.1 範例：LangGraph + LangSmith 完整整合
# 包含 tracing、metadata、自訂 tag
# 需要：pip install langgraph langchain-openai langchain-core
# 需要：設定 LANGSMITH_API_KEY 和 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 環境變數

import os
from typing import Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

# === 環境設定 ===
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_xxxxx"
os.environ["OPENAI_API_KEY"] = "sk-xxxxx"


# === 工具定義 ===
@tool
def calculator(expression: str) -> str:
    """計算數學表達式"""
    try:
        result = eval(expression)  # 注意：生產環境請用安全的 eval
        return str(result)
    except Exception as e:
        return f"計算錯誤: {e}"


@tool
def get_weather(city: str) -> str:
    """查詢城市天氣"""
    weather_data = {
        "台北": "28度，多雲",
        "東京": "22度，晴天",
        "紐約": "15度，陰天",
    }
    return weather_data.get(city, f"找不到 {city} 的天氣資料")


# === 建構 Agent ===
tools = [calculator, get_weather]
tool_node = ToolNode(tools)
#model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)  # Set OPENAI_API_KEY in environment variables, you could create API key at https://platform.openai.com/settings/organization/api-keys
model = ChatAnthropic(model="claude-sonnet-4-5").bind_tools(tools)  # Set ANTHROPIC_API_KEY in environment variables, you could create API key at https://platform.claude.com/settings/keys


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    if state["messages"][-1].tool_calls:
        return "tools"
    return "__end__"


def call_model(state: MessagesState) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response]}


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
app = workflow.compile()


# === 執行時加入追蹤 metadata ===
def run_agent(user_input: str, user_id: str = "user_001"):
    """執行 agent 並附帶追蹤 metadata"""
    result = app.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config={
            "configurable": {"thread_id": f"thread_{user_id}"},
            # metadata 和 tags 會出現在 LangSmith trace 中
            "metadata": {
                "user_id": user_id,
                "environment": "development",
                "version": "v1.0",
            },
            "tags": ["production", "agent-v1"],
        },
    )
    return result["messages"][-1].content


# === 測試 ===
if __name__ == "__main__":
    # 這些呼叫都會產生 traces 並出現在 LangSmith Dashboard
    print(run_agent("台北天氣如何？"))
    print(run_agent("計算 123 * 456"))
    print(run_agent("東京天氣怎麼樣？然後幫我算 100 / 3"))
