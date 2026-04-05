# 16.2 範例：完整的錯誤處理
# 結合所有策略：RetryPolicy、LLM Recovery、interrupt、Graceful Degradation
# 需要：pip install langgraph

from typing import Annotated, Literal
from typing_extensions import TypedDict
from operator import add

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy, Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.managed import RemainingSteps


class AgentState(TypedDict):
    messages: Annotated[list[str], add]
    error_log: Annotated[list[str], add]
    tool_result: str
    remaining_steps: RemainingSteps


# ============================================================
# 策略 1：Transient Error -> RetryPolicy 自動重試
# ============================================================
def fetch_data(state: AgentState) -> dict:
    """外部 API 呼叫 — 自動重試暫時性錯誤"""
    import random
    if random.random() < 0.3:  # 30% 機率失敗
        raise ConnectionError("Network timeout")
    return {
        "tool_result": "data fetched successfully",
        "messages": ["資料擷取成功"],
    }


# ============================================================
# 策略 2：LLM-Recoverable -> 存入 state 讓 LLM 重試
# ============================================================
def execute_tool(state: AgentState) -> Command[Literal["agent", "execute_tool"]]:
    """工具執行 — 失敗時將錯誤回傳給 LLM"""
    try:
        # 模擬工具執行
        result = f"Tool executed with: {state['tool_result']}"
        return Command(
            update={"tool_result": result, "messages": ["工具執行成功"]},
            goto="agent",
        )
    except Exception as e:
        # 將錯誤資訊存入 state，讓 LLM 看到並調整策略
        return Command(
            update={
                "tool_result": f"Tool error: {str(e)}",
                "error_log": [f"Tool failed: {e}"],
                "messages": [f"工具失敗: {e}，LLM 將調整策略"],
            },
            goto="agent",
        )


# ============================================================
# 策略 3：User-fixable -> interrupt() 等待人類輸入
# ============================================================
def require_confirmation(state: AgentState) -> Command[Literal["proceed", "__end__"]]:
    """需要使用者確認的操作"""
    user_input = interrupt({
        "message": "需要確認",
        "question": "是否繼續執行這個操作？",
        "context": state["messages"][-3:],
    })

    if user_input.get("confirmed"):
        return Command(
            update={"messages": ["使用者已確認"]},
            goto="proceed",
        )
    return Command(
        update={"messages": ["使用者取消操作"]},
        goto="__end__",
    )


# ============================================================
# 策略 4：Recursion Limit -> RemainingSteps 優雅降級
# ============================================================
def agent(state: AgentState) -> Command[Literal["fetch_data", "execute_tool", "require_confirmation", "__end__"]]:
    """Agent 主節點 — 結合所有錯誤處理策略"""
    remaining = state["remaining_steps"]

    # 主動檢查 recursion limit
    if remaining <= 2:
        return Command(
            update={"messages": ["接近步驟限制，提供當前最佳結果"]},
            goto="__end__",
        )

    # 檢查是否有工具錯誤需要處理
    if state.get("tool_result", "").startswith("Tool error"):
        return Command(
            update={"messages": ["偵測到錯誤，嘗試替代方案"]},
            goto="fetch_data",  # 嘗試重新擷取資料
        )

    # 正常流程
    if not state.get("tool_result"):
        return Command(goto="fetch_data")
    else:
        return Command(goto="require_confirmation")


def proceed(state: AgentState) -> dict:
    """最終處理"""
    return {"messages": [f"處理完成！結果: {state['tool_result']}"]}


# ============================================================
# 建構 Graph
# ============================================================
builder = StateGraph(AgentState)

builder.add_node("agent", agent)
builder.add_node(
    "fetch_data",
    fetch_data,
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=0.5),
)
builder.add_node("execute_tool", execute_tool)
builder.add_node("require_confirmation", require_confirmation)
builder.add_node("proceed", proceed)

builder.add_edge(START, "agent")
builder.add_edge("proceed", END)

graph = builder.compile(checkpointer=InMemorySaver())

# ============================================================
# 執行
# ============================================================
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "error-handling-demo"}}

    print("=== 開始執行 ===")
    result = graph.invoke(
        {
            "messages": ["開始"],
            "error_log": [],
            "tool_result": "",
        },
        config,
        {"recursion_limit": 20},
    )
    print(f"\n結果: {result['messages']}")

    if result.get("error_log"):
        print(f"錯誤紀錄: {result['error_log']}")
