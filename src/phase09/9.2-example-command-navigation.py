# 9.2 範例：透過 Command 從子圖導航到父圖節點
# Agent A 分析任務後，依結果透過 Command(graph=Command.PARENT) 導航到 Agent B 或 Reporter。

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

# ============================================================
# 1. 定義共享 State
# ============================================================
class TeamState(TypedDict):
    task: str
    analysis: str
    execution_result: str
    logs: Annotated[list[str], lambda x, y: x + y]
    next_action: str  # "execute" 或 "report"


# ============================================================
# 2. 子圖 A：分析 Agent
# ============================================================
def analyze_task(state: TeamState) -> dict:
    """分析任務"""
    task = state.get("task", "")
    needs_execution = "執行" in task or "建立" in task
    return {
        "analysis": f"分析結果：任務 '{task}' {'需要' if needs_execution else '不需要'}執行操作",
        "next_action": "execute" if needs_execution else "report",
        "logs": [f"[Agent A] 完成分析，下一步: {'execute' if needs_execution else 'report'}"]
    }

def decide_and_navigate(state: TeamState) -> Command:
    """
    根據分析結果，使用 Command 導航到父圖中的不同節點。
    這是子圖跳出到父圖的關鍵步驟。
    """
    next_action = state.get("next_action", "report")

    if next_action == "execute":
        # 導航到父圖的 "agent_b" 節點
        return Command(
            goto="agent_b",
            update={
                "logs": ["[Agent A -> Agent B] 移交執行任務"]
            },
            graph=Command.PARENT    # <-- 關鍵：指向父圖
        )
    else:
        # 導航到父圖的 "reporter" 節點
        return Command(
            goto="reporter",
            update={
                "logs": ["[Agent A -> Reporter] 直接生成報告"]
            },
            graph=Command.PARENT    # <-- 關鍵：指向父圖
        )

agent_a_builder = StateGraph(TeamState)
agent_a_builder.add_node("analyze", analyze_task)
agent_a_builder.add_node("decide", decide_and_navigate)
agent_a_builder.add_edge(START, "analyze")
agent_a_builder.add_edge("analyze", "decide")
# 注意：decide 節點不需要加 edge 到 END，因為它透過 Command 離開子圖
agent_a_subgraph = agent_a_builder.compile()


# ============================================================
# 3. 子圖 B：執行 Agent
# ============================================================
def execute_task(state: TeamState) -> dict:
    """執行任務"""
    return {
        "execution_result": f"已執行: {state.get('task', '')}",
        "logs": ["[Agent B] 執行完成"]
    }

def navigate_to_reporter(state: TeamState) -> Command:
    """執行完成後，導航回父圖的 reporter"""
    return Command(
        goto="reporter",
        update={
            "logs": ["[Agent B -> Reporter] 執行完畢，移交報告生成"]
        },
        graph=Command.PARENT
    )

agent_b_builder = StateGraph(TeamState)
agent_b_builder.add_node("execute", execute_task)
agent_b_builder.add_node("nav_report", navigate_to_reporter)
agent_b_builder.add_edge(START, "execute")
agent_b_builder.add_edge("execute", "nav_report")
agent_b_subgraph = agent_b_builder.compile()


# ============================================================
# 4. 父圖的普通節點
# ============================================================
def generate_report(state: TeamState) -> dict:
    """生成最終報告"""
    analysis = state.get("analysis", "無")
    execution = state.get("execution_result", "無")
    return {
        "logs": [f"[Reporter] 報告生成完成 | 分析: {analysis} | 執行: {execution}"]
    }


# ============================================================
# 5. 建立父圖
# ============================================================
parent_builder = StateGraph(TeamState)
parent_builder.add_node("agent_a", agent_a_subgraph)
parent_builder.add_node("agent_b", agent_b_subgraph)
parent_builder.add_node("reporter", generate_report)

parent_builder.add_edge(START, "agent_a")
# agent_a 和 agent_b 的導航由 Command 處理，不需要靜態 edge
parent_builder.add_edge("reporter", END)

parent_graph = parent_builder.compile()


# ============================================================
# 6. 執行測試
# ============================================================
# 測試案例 1：需要執行的任務
print("=== 案例 1：需要執行 ===")
result1 = parent_graph.invoke({
    "task": "建立新的資料庫索引",
    "analysis": "",
    "execution_result": "",
    "logs": [],
    "next_action": ""
})
for log in result1["logs"]:
    print(f"  {log}")

print("\n=== 案例 2：只需報告 ===")
result2 = parent_graph.invoke({
    "task": "查詢系統狀態",
    "analysis": "",
    "execution_result": "",
    "logs": [],
    "next_action": ""
})
for log in result2["logs"]:
    print(f"  {log}")
