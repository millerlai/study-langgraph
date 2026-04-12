# 3.3 範例：多路由平行分發（使用 Send + 真實 Anthropic LLM）
# 展示一個請求同時交給多個 Agent 處理的平行路由模式。
# 需要環境變數 ANTHROPIC_API_KEY

from typing import Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from dotenv import load_dotenv
import operator, sys, io

load_dotenv()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# 1. 定義 LLM 多路由決策的 structured output schema
class MultiRouteDecision(BaseModel):
    """LLM 多路由決策結果"""
    agents: list[str] = Field(
        description="需要分派的 Agent 列表，可選值：research, code, write, chat"
    )
    reasoning: str = Field(
        description="選擇這些 Agent 的理由（一句話）"
    )


# 2. 定義 State
class MultiRouterState(TypedDict):
    query: str
    selected_agents: list[str]
    reasoning: str
    results: Annotated[list[str], operator.add]
    final_answer: str


class AgentInput(TypedDict):
    query: str
    agent_name: str


# 3. 初始化 LLM
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
router_llm = llm.with_structured_output(MultiRouteDecision)


# 4. 定義 Node 函數
def multi_router(state: MultiRouterState) -> dict:
    """使用真實 LLM 進行多路由決策"""
    decision: MultiRouteDecision = router_llm.invoke(
        "你是一個任務分派器。根據使用者的查詢，判斷需要哪些 Agent 來處理。\n"
        "可用的 Agent：\n"
        "- research：研究分析（需要調查、比較、分析時）\n"
        "- code：程式開發（需要寫程式、解 bug 時）\n"
        "- write：文章寫作（需要撰寫文章、報告時）\n"
        "- chat：一般聊天（以上都不符合時）\n\n"
        "一個查詢可以同時需要多個 Agent。\n\n"
        f"使用者查詢：{state['query']}"
    )
    print(f"[multi_router] 查詢='{state['query']}' -> 分派給: {decision.agents} (理由: {decision.reasoning})")
    return {"selected_agents": decision.agents, "reasoning": decision.reasoning}


def dispatch_agents(state: MultiRouterState):
    """Send 路由函數：動態分派到多個 Agent"""
    return [
        Send("agent_worker", {"query": state["query"], "agent_name": agent})
        for agent in state["selected_agents"]
    ]


def agent_worker(state: AgentInput) -> dict:
    """通用 Agent Worker：使用 LLM 處理各類型任務"""
    agent = state["agent_name"]
    query = state["query"]

    prompts = {
        "research": f"你是研究分析專家。請針對以下問題提供簡短的研究摘要（2-3句話）：\n\n{query}",
        "code": f"你是程式設計專家。請針對以下需求提供簡短的技術方案（2-3句話）：\n\n{query}",
        "write": f"你是寫作專家。請針對以下需求提供簡短的寫作大綱（2-3句話）：\n\n{query}",
        "chat": f"你是友善的聊天助手。請簡短回應：\n\n{query}",
    }
    response = llm.invoke(prompts.get(agent, prompts["chat"]))
    result = f"[{agent}] {response.content}"
    print(f"[agent_worker:{agent}] 處理完成")
    return {"results": [result]}


def synthesize(state: MultiRouterState) -> dict:
    """使用 LLM 合成所有 Agent 的結果"""
    results_text = "\n".join(state["results"])
    response = llm.invoke(
        f"你是一位總結專家。以下是多個 Agent 針對使用者查詢的分析結果，"
        f"請將它們整合成一個連貫的最終回答（3-5句話）。\n\n"
        f"使用者查詢：{state['query']}\n\n"
        f"各 Agent 結果：\n{results_text}"
    )
    print(f"[synthesize] 合成 {len(state['results'])} 個結果")
    return {"final_answer": response.content}


# 5. 建構 Graph
builder = StateGraph(MultiRouterState)
builder.add_node("multi_router", multi_router)
builder.add_node("agent_worker", agent_worker)
builder.add_node("synthesize", synthesize)

builder.add_edge(START, "multi_router")
builder.add_conditional_edges("multi_router", dispatch_agents, ["agent_worker"])
builder.add_edge("agent_worker", "synthesize")
builder.add_edge("synthesize", END)

graph = builder.compile()

# 6. 測試：一個請求觸發多個 Agent
result = graph.invoke({
    "query": "研究 Python 的非同步程式設計，並寫一篇分析報告",
    "selected_agents": [],
    "reasoning": "",
    "results": [],
    "final_answer": "",
})

print(f"\n=== 最終答案 ===")
print(f"路由: {result['selected_agents']}")
print(f"理由: {result['reasoning']}")
print(f"答案:\n{result['final_answer']}")
