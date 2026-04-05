# 3.1 範例：迴圈 + 分支組合（多工具 Agent 迴圈）
# 展示迴圈中搭配條件邊選擇不同工具的 Agent 模式。

from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義 State
class AgentState(TypedDict):
    query: str
    steps: list[str]
    data: dict
    answer: str
    iteration: int


# 2. 定義 Node 函數
def thinking(state: AgentState) -> dict:
    """Agent 思考：根據目前狀態決定下一步"""
    iteration = state["iteration"] + 1
    steps = state.get("steps", []) + [f"思考中 (迭代 {iteration})..."]
    print(f"[thinking] 迭代 {iteration}, 已收集資料: {list(state.get('data', {}).keys())}")
    return {"steps": steps, "iteration": iteration}


def tool_search(state: AgentState) -> dict:
    """搜尋工具"""
    result = f"搜尋結果：找到 '{state['query']}' 的相關資訊"
    print(f"[tool_search] {result}")
    data = {**state.get("data", {}), "search": result}
    steps = state.get("steps", []) + ["執行搜尋"]
    return {"data": data, "steps": steps}


def tool_calc(state: AgentState) -> dict:
    """計算工具"""
    result = "計算結果：42"
    print(f"[tool_calc] {result}")
    data = {**state.get("data", {}), "calc": result}
    steps = state.get("steps", []) + ["執行計算"]
    return {"data": data, "steps": steps}


def tool_summarize(state: AgentState) -> dict:
    """摘要工具"""
    collected = state.get("data", {})
    result = f"摘要：基於 {len(collected)} 個資料來源的綜合結論"
    print(f"[tool_summarize] {result}")
    data = {**collected, "summary": result}
    steps = state.get("steps", []) + ["執行摘要"]
    return {"data": data, "steps": steps}


# 3. 定義路由函數
def decide_action(state: AgentState) -> str:
    """決定下一步動作：選擇工具或結束"""
    data = state.get("data", {})
    iteration = state["iteration"]

    # 模擬 agent 邏輯：依序使用工具，最後結束
    if "search" not in data:
        return "tool_search"
    elif "calc" not in data:
        return "tool_calc"
    elif "summary" not in data:
        return "tool_summarize"
    else:
        return "finish"


def generate_answer(state: AgentState) -> dict:
    """產生最終答案"""
    data = state.get("data", {})
    answer = f"最終答案（基於 {len(data)} 個步驟的分析）：所有工具呼叫完成"
    print(f"[generate_answer] {answer}")
    steps = state.get("steps", []) + ["產生最終答案"]
    return {"answer": answer, "steps": steps}


# 4. 建構 Graph（迴圈 + 分支）
builder = StateGraph(AgentState)
builder.add_node("thinking", thinking)
builder.add_node("tool_search", tool_search)
builder.add_node("tool_calc", tool_calc)
builder.add_node("tool_summarize", tool_summarize)
builder.add_node("generate_answer", generate_answer)

# 入口
builder.add_edge(START, "thinking")

# 條件分支：thinking 後選擇工具或結束
builder.add_conditional_edges(
    "thinking",
    decide_action,
    {
        "tool_search": "tool_search",
        "tool_calc": "tool_calc",
        "tool_summarize": "tool_summarize",
        "finish": "generate_answer",
    }
)

# 所有工具執行完後回到 thinking（形成迴圈）
builder.add_edge("tool_search", "thinking")
builder.add_edge("tool_calc", "thinking")
builder.add_edge("tool_summarize", "thinking")

# 最終答案後結束
builder.add_edge("generate_answer", END)

graph = builder.compile()

# 5. 執行
result = graph.invoke({
    "query": "LangGraph 是什麼？",
    "steps": [],
    "data": {},
    "answer": "",
    "iteration": 0,
})

print(f"\n=== 執行結果 ===")
print(f"答案: {result['answer']}")
print(f"總迭代: {result['iteration']}")
print(f"步驟紀錄:")
for i, step in enumerate(result["steps"], 1):
    print(f"  {i}. {step}")
