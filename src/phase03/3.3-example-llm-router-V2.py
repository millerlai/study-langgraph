# 3.3 範例 V2：真實 LLM 路由器（Anthropic Claude 驅動的動態路由）
# 使用 ChatAnthropic + structured output 實現語意分類路由
# 需要環境變數 ANTHROPIC_API_KEY

from typing import Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from dotenv import load_dotenv
load_dotenv()

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# 1. 定義路由決策的 structured output schema
class RouteDecision(BaseModel):
    """LLM 路由決策結果"""
    route: Literal["research", "code", "write", "chat"] = Field(
        description="分類結果：research=研究分析, code=程式開發, write=文章寫作, chat=一般聊天"
    )
    reasoning: str = Field(
        description="選擇此分類的理由（一句話）"
    )


# 2. 定義 State
class RouterState(TypedDict):
    user_input: str
    route: str
    reasoning: str
    result: str


# 3. 初始化 LLM（使用 structured output）
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
router_llm = llm.with_structured_output(RouteDecision)


# 4. 定義 Node 函數
def llm_router(state: RouterState) -> Command[
    Literal["research_agent", "code_agent", "write_agent", "chat_agent"]
]:
    """使用真實 LLM 進行語意分類路由"""
    decision: RouteDecision = router_llm.invoke(
        f"你是一個路由分類器。根據使用者輸入，判斷應該由哪個 Agent 處理。\n\n"
        f"使用者輸入：{state['user_input']}"
    )
    print(f"[llm_router] 輸入='{state['user_input']}' -> 路由='{decision.route}' (理由: {decision.reasoning})")

    route_map = {
        "research": "research_agent",
        "code": "code_agent",
        "write": "write_agent",
        "chat": "chat_agent",
    }
    return Command(
        update={"route": decision.route, "reasoning": decision.reasoning},
        goto=route_map[decision.route],
    )


def research_agent(state: RouterState) -> dict:
    """研究 Agent：使用 LLM 進行研究分析"""
    response = llm.invoke(
        f"你是一位研究分析專家。請針對以下問題提供簡短的研究摘要（3-5句話）：\n\n{state['user_input']}"
    )
    print(f"[research_agent] 執行研究任務")
    return {"result": response.content}


def code_agent(state: RouterState) -> dict:
    """程式 Agent：使用 LLM 產生程式碼"""
    response = llm.invoke(
        f"你是一位程式設計專家。請針對以下需求提供簡潔的程式碼解決方案：\n\n{state['user_input']}"
    )
    print(f"[code_agent] 執行程式任務")
    return {"result": response.content}


def write_agent(state: RouterState) -> dict:
    """寫作 Agent：使用 LLM 進行寫作"""
    response = llm.invoke(
        f"你是一位寫作專家。請針對以下需求提供簡短的文章草稿（3-5段）：\n\n{state['user_input']}"
    )
    print(f"[write_agent] 執行寫作任務")
    return {"result": response.content}


def chat_agent(state: RouterState) -> dict:
    """聊天 Agent：使用 LLM 進行一般對話"""
    response = llm.invoke(
        f"你是一位友善的聊天助手。請回應以下訊息：\n\n{state['user_input']}"
    )
    print(f"[chat_agent] 執行聊天任務")
    return {"result": response.content}


# 5. 建構 Graph
builder = StateGraph(RouterState)
builder.add_node("llm_router", llm_router)
builder.add_node("research_agent", research_agent)
builder.add_node("code_agent", code_agent)
builder.add_node("write_agent", write_agent)
builder.add_node("chat_agent", chat_agent)

builder.add_edge(START, "llm_router")
builder.add_edge("research_agent", END)
builder.add_edge("code_agent", END)
builder.add_edge("write_agent", END)
builder.add_edge("chat_agent", END)

graph = builder.compile()

# 6. 測試不同輸入
test_inputs = [
    "幫我研究一下 LangGraph 和 AutoGen 的比較",
    "寫一個 Python 的快速排序程式",
    "幫我寫一篇關於 AI Agent 的文章草稿",
    "今天天氣真好",
]

for user_input in test_inputs:
    print(f"\n{'='*60}")
    result = graph.invoke({
        "user_input": user_input,
        "route": "",
        "reasoning": "",
        "result": "",
    })
    print(f"路由: {result['route']}")
    print(f"理由: {result['reasoning']}")
    print(f"結果: {result['result'][:200]}...")
