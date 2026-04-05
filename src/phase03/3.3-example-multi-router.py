# 3.3 範例：多路由平行分發（使用 Send）
# 展示一個請求同時交給多個 Agent 處理的平行路由模式。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator


# 1. 定義 State
class MultiRouterState(TypedDict):
    query: str
    selected_agents: list[str]
    results: Annotated[list[str], operator.add]
    final_answer: str


class AgentInput(TypedDict):
    query: str
    agent_name: str


# 2. 模擬 LLM 多路由決策
def simulate_llm_multi_route(query: str) -> list[str]:
    """
    模擬 LLM 決定需要哪些 Agent。
    實際應用中，LLM 可能回傳：
    {"agents": ["research", "code"], "reasoning": "這個問題需要研究+寫程式"}
    """
    query_lower = query.lower()
    agents = []
    if any(w in query_lower for w in ["研究", "分析", "比較"]):
        agents.append("research")
    if any(w in query_lower for w in ["程式", "code", "python"]):
        agents.append("code")
    if any(w in query_lower for w in ["寫", "文章", "報告"]):
        agents.append("write")
    return agents if agents else ["chat"]


# 3. 定義 Node 函數
def multi_router(state: MultiRouterState) -> dict:
    """多路由決策節點"""
    agents = simulate_llm_multi_route(state["query"])
    print(f"[multi_router] 查詢='{state['query']}' -> 分派給: {agents}")
    return {"selected_agents": agents}


def dispatch_agents(state: MultiRouterState):
    """Send 路由函數：動態分派到多個 Agent"""
    return [
        Send("agent_worker", {"query": state["query"], "agent_name": agent})
        for agent in state["selected_agents"]
    ]


def agent_worker(state: AgentInput) -> dict:
    """通用 Agent Worker"""
    agent = state["agent_name"]
    query = state["query"]
    result = f"[{agent}] 針對 '{query}' 的分析結果"
    print(f"[agent_worker:{agent}] 處理完成")
    return {"results": [result]}


def synthesize(state: MultiRouterState) -> dict:
    """合成所有 Agent 的結果"""
    results = state["results"]
    answer = f"綜合 {len(results)} 個 Agent 的結果：\n"
    for r in results:
        answer += f"  - {r}\n"
    print(f"[synthesize] 合成 {len(results)} 個結果")
    return {"final_answer": answer}


# 4. 建構 Graph
builder = StateGraph(MultiRouterState)
builder.add_node("multi_router", multi_router)
builder.add_node("agent_worker", agent_worker)
builder.add_node("synthesize", synthesize)

builder.add_edge(START, "multi_router")
builder.add_conditional_edges("multi_router", dispatch_agents, ["agent_worker"])
builder.add_edge("agent_worker", "synthesize")
builder.add_edge("synthesize", END)

graph = builder.compile()

# 5. 測試：一個請求觸發多個 Agent
result = graph.invoke({
    "query": "研究 Python 的非同步程式設計，並寫一篇分析報告",
    "selected_agents": [],
    "results": [],
    "final_answer": "",
})

print(f"\n=== 最終答案 ===")
print(result["final_answer"])
