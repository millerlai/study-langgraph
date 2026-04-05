# 1.1 LangGraph 概觀 — Multi-Agent 協作範例
# 展示 Supervisor 模式：主管決策 + 多個 Agent 協作
# 不需要 API key（使用模擬邏輯）

from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
import operator

# 1. 定義共享 State
class TeamState(TypedDict):
    topic: str                                          # 要處理的主題
    research: str                                       # 研究結果
    draft: str                                          # 文章草稿
    messages: Annotated[list[str], operator.add]        # 工作日誌（用 reducer 累加）
    next_agent: str                                     # Supervisor 指派的下一位

# 2. Supervisor（主管）——決定下一步交給誰
def supervisor(state: TeamState) -> dict:
    """根據目前進度決定下一步"""
    if not state.get("research"):
        # 還沒研究 → 交給 researcher
        return {
            "next_agent": "researcher",
            "messages": ["[Supervisor] 請 Researcher 先蒐集資料"],
        }
    elif not state.get("draft"):
        # 有研究但沒草稿 → 交給 writer
        return {
            "next_agent": "writer",
            "messages": ["[Supervisor] 資料已備，請 Writer 撰寫文章"],
        }
    else:
        # 都完成了 → 結束
        return {
            "next_agent": "FINISH",
            "messages": ["[Supervisor] 文章完成，任務結束"],
        }

# 3. Research Agent
def researcher(state: TeamState) -> dict:
    """蒐集主題相關資料"""
    topic = state["topic"]
    # 實際應用中這裡會呼叫 LLM 或搜尋工具
    research = f"關於「{topic}」的研究摘要：這是一個重要的技術趨勢..."
    return {
        "research": research,
        "messages": [f"[Researcher] 已完成「{topic}」的研究"],
    }

# 4. Writer Agent
def writer(state: TeamState) -> dict:
    """根據研究結果撰寫文章"""
    research = state["research"]
    # 實際應用中這裡會呼叫 LLM 生成文章
    draft = f"文章草稿：根據研究——{research}——我們可以得出以下結論..."
    return {
        "draft": draft,
        "messages": ["[Writer] 已完成文章草稿"],
    }

# 5. 路由函數——根據 Supervisor 的決定導向對應節點
def route_next(state: TeamState) -> Literal["researcher", "writer", "__end__"]:
    next_agent = state["next_agent"]
    if next_agent == "FINISH":
        return END
    return next_agent

# 6. 建構 Graph
builder = StateGraph(TeamState)

builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

# 起點 → Supervisor
builder.add_edge(START, "supervisor")

# Supervisor → 條件路由（交給 researcher / writer / 結束）
builder.add_conditional_edges("supervisor", route_next, ["researcher", "writer", END])

# 各 Agent 完成後 → 回到 Supervisor 重新決策
builder.add_edge("researcher", "supervisor")
builder.add_edge("writer", "supervisor")

graph = builder.compile()

# 7. 執行
result = graph.invoke({
    "topic": "LangGraph 多代理架構",
    "research": "",
    "draft": "",
    "messages": [],
    "next_agent": "",
})

print(result["draft"])
print("\n--- 工作日誌 ---")
for msg in result["messages"]:
    print(msg)
