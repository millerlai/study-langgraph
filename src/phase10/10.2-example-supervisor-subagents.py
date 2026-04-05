# 10.2 範例：使用 create_agent 實現 Supervisor 模式（Subagents 模式）
# 這是 LangChain v1 推薦的模式：子 Agent 包裝為 Tool，Supervisor 透過 Tool 呼叫子 Agent。
#
# 注意：此範例需要以下依賴和設定：
#   - langchain>=1.0
#   - 有效的 LLM API Key（如 ANTHROPIC_API_KEY）
#   - uv add langchain langchain-anthropic

from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# ============================================================
# 1. 定義底層工具（子 Agent 使用的）
# ============================================================
@tool
def search_database(query: str) -> str:
    """搜尋資料庫中的資料。"""
    # 模擬資料庫搜尋
    return f"搜尋結果: 找到 3 筆關於「{query}」的記錄"

@tool
def generate_chart(data_description: str) -> str:
    """根據資料描述生成圖表。"""
    return f"圖表已生成: {data_description} 的視覺化圖表"

@tool
def send_notification(recipient: str, message: str) -> str:
    """發送通知訊息。"""
    return f"通知已發送給 {recipient}: {message}"


# ============================================================
# 2. 建立子 Agent
# ============================================================
model = init_chat_model("anthropic:claude-sonnet-4-20250514")

# 資料分析 Agent
data_agent = create_agent(
    model,
    tools=[search_database, generate_chart],
    system_prompt=(
        "你是資料分析專家。負責搜尋資料庫、分析資料、生成圖表。"
        "完成分析後，在最後回覆中包含所有分析結果。"
    ),
)

# 通知 Agent
notification_agent = create_agent(
    model,
    tools=[send_notification],
    system_prompt=(
        "你是通知管理專家。負責根據需求發送適當的通知。"
        "確認通知發送後，在最後回覆中確認發送狀態。"
    ),
)


# ============================================================
# 3. 包裝子 Agent 為 Tool（Supervisor 使用的）
# ============================================================
@tool
def analyze_data(request: str) -> str:
    """進行資料分析。包含搜尋資料庫、統計分析、圖表生成。

    輸入: 自然語言的分析需求描述。
    """
    result = data_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def send_alerts(request: str) -> str:
    """發送通知和警報。包含訊息撰寫和發送。

    輸入: 自然語言的通知需求描述。
    """
    result = notification_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text


# ============================================================
# 4. 建立 Supervisor Agent
# ============================================================
supervisor = create_agent(
    model,
    tools=[analyze_data, send_alerts],
    system_prompt=(
        "你是專案管理助理。你可以進行資料分析和發送通知。"
        "根據用戶需求，選擇適當的工具來完成任務。"
        "如果任務涉及多個步驟，按順序呼叫多個工具。"
    ),
)


# ============================================================
# 5. 使用 Supervisor
# ============================================================
if __name__ == "__main__":
    # 複合任務：先分析再通知
    query = "分析上個月的銷售數據，然後通知銷售團隊本月目標"

    for step in supervisor.stream(
        {"messages": [{"role": "user", "content": query}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
