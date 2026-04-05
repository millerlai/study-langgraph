# 10.2 範例：使用 Command + ToolMessage 實現標準 Handoff（Swarm 模式）
# 定義 Handoff 工具返回 Command，包含 AIMessage + ToolMessage 確保對話歷史完整。
#
# 注意：此範例需要以下依賴和設定：
#   - langchain>=1.0
#   - 有效的 LLM API Key（如 ANTHROPIC_API_KEY）
#   - uv add langchain langchain-anthropic

from typing import Literal

from langchain.agents import create_agent
from langchain.agents import AgentState
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import NotRequired

# ============================================================
# 1. 定義 State
# ============================================================
class MultiAgentState(AgentState):
    active_agent: NotRequired[str]


# ============================================================
# 2. 定義 Handoff 工具
# ============================================================
@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """轉接到銷售 Agent。當用戶詢問價格、購買、方案時使用。"""
    # 取得觸發 handoff 的 AI 訊息
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"])
        if isinstance(msg, AIMessage)
    )
    # 建立 ToolMessage 完成 tool call 的 request-response 循環
    transfer_message = ToolMessage(
        content="已轉接到銷售 Agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )


@tool
def transfer_to_support(
    runtime: ToolRuntime,
) -> Command:
    """轉接到客服 Agent。當用戶遇到問題、需要幫助時使用。"""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"])
        if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="已轉接到客服 Agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="support_agent",
        update={
            "active_agent": "support_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )


# ============================================================
# 3. 建立 Agent
# ============================================================
model = init_chat_model("anthropic:claude-sonnet-4-20250514")

sales_agent = create_agent(
    model,
    tools=[transfer_to_support],
    system_prompt="你是銷售顧問。幫助用戶了解產品方案和價格。"
                  "如果用戶有技術問題或需要客服支援，使用 transfer_to_support 轉接。",
)

support_agent = create_agent(
    model,
    tools=[transfer_to_sales],
    system_prompt="你是客服顧問。幫助用戶解決問題。"
                  "如果用戶詢問價格或想購買，使用 transfer_to_sales 轉接。",
)


# ============================================================
# 4. 建立 Agent 節點
# ============================================================
def call_sales(state: MultiAgentState) -> Command:
    response = sales_agent.invoke(state)
    return response

def call_support(state: MultiAgentState) -> Command:
    response = support_agent.invoke(state)
    return response


# ============================================================
# 5. 路由邏輯
# ============================================================
def route_after_agent(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent", "__end__"]:
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        # AI 回覆且沒有 tool call = Agent 已完成
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            return "__end__"
    active = state.get("active_agent", "sales_agent")
    return active if active else "sales_agent"

def route_initial(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent"]:
    return state.get("active_agent") or "sales_agent"


# ============================================================
# 6. 建立父圖
# ============================================================
builder = StateGraph(MultiAgentState)
builder.add_node("sales_agent", call_sales)
builder.add_node("support_agent", call_support)

builder.add_conditional_edges(
    START, route_initial,
    ["sales_agent", "support_agent"]
)
builder.add_conditional_edges(
    "sales_agent", route_after_agent,
    ["sales_agent", "support_agent", END]
)
builder.add_conditional_edges(
    "support_agent", route_after_agent,
    ["sales_agent", "support_agent", END]
)

graph = builder.compile()

# ============================================================
# 7. 使用
# ============================================================
if __name__ == "__main__":
    result = graph.invoke({
        "messages": [
            {"role": "user", "content": "我的帳號登入有問題，可以幫忙嗎？"}
        ]
    })
    for msg in result["messages"]:
        msg.pretty_print()
