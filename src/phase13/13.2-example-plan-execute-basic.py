# 13.2 範例：基本 Plan-and-Execute Agent
# 將任務分解為步驟，然後逐步執行
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai

import os
from typing import TypedDict, Annotated
import operator
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END

os.environ["OPENAI_API_KEY"] = "your-api-key"


# ---- State 定義 ----
class PlanStep(BaseModel):
    """單一計畫步驟"""
    step_number: int = Field(description="步驟編號")
    description: str = Field(description="步驟描述")
    tool_needed: str = Field(description="需要的工具名稱，若不需要工具則為 'none'")


class Plan(BaseModel):
    """完整執行計畫"""
    steps: list[PlanStep] = Field(description="按順序排列的步驟列表")


class PlanExecuteState(TypedDict):
    """Agent 的完整狀態"""
    task: str                                          # 原始任務
    plan: list[dict]                                   # 計畫步驟列表
    current_step_index: int                            # 當前執行到第幾步
    step_results: Annotated[list[str], operator.add]   # 每步的執行結果
    final_answer: str                                  # 最終回答


# ---- 工具定義 ----
@tool
def calculator(expression: str) -> str:
    """計算數學表達式。輸入一個合法的 Python 數學表達式字串。"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"計算結果：{expression} = {result}"
    except Exception as e:
        return f"計算錯誤：{e}"


@tool
def search_knowledge(query: str) -> str:
    """搜尋知識庫（模擬）。輸入搜尋關鍵字。"""
    # 模擬搜尋結果
    knowledge_base = {
        "台灣人口": "台灣人口約為 2,340 萬人（2024 年）",
        "日本人口": "日本人口約為 1.25 億人（2024 年）",
        "GDP": "台灣 2024 年 GDP 約為 7,900 億美元",
        "面積": "台灣面積約 36,193 平方公里",
    }
    for key, value in knowledge_base.items():
        if key in query:
            return value
    return f"找到關於「{query}」的資訊：[模擬搜尋結果]"


TOOLS = [calculator, search_knowledge]
TOOL_MAP = {t.name: t for t in TOOLS}

# ---- LLM ----
planner_llm = init_chat_model("gpt-4o-mini", temperature=0)
executor_llm = init_chat_model("gpt-4o-mini", temperature=0)


# ---- 規劃節點 ----
def planner(state: PlanExecuteState):
    """將任務分解為可執行的步驟"""
    task = state["task"]
    tool_descriptions = "\n".join(
        [f"- {t.name}: {t.description}" for t in TOOLS]
    )

    prompt = (
        "你是一個任務規劃器。將以下任務分解為明確的執行步驟。\n"
        "每個步驟應該是具體、可執行的。\n\n"
        f"可用的工具：\n{tool_descriptions}\n\n"
        f"任務：{task}\n\n"
        "請制定執行計畫。最後一個步驟應該是「彙整結果並回答」。"
    )

    plan = planner_llm.with_structured_output(Plan).invoke(
        [{"role": "user", "content": prompt}]
    )

    plan_dicts = [step.model_dump() for step in plan.steps]
    print("  [規劃器] 制定的計畫：")
    for step in plan.steps:
        print(f"    步驟 {step.step_number}: {step.description} (工具: {step.tool_needed})")

    return {
        "plan": plan_dicts,
        "current_step_index": 0,
    }


# ---- 執行節點 ----
def executor(state: PlanExecuteState):
    """執行當前步驟"""
    idx = state["current_step_index"]
    plan = state["plan"]

    if idx >= len(plan):
        return {"step_results": ["所有步驟已完成"]}

    current_step = plan[idx]
    step_desc = current_step["description"]
    tool_name = current_step["tool_needed"]

    print(f"\n  [執行器] 執行步驟 {idx + 1}: {step_desc}")

    if tool_name != "none" and tool_name in TOOL_MAP:
        # 讓 LLM 決定工具的輸入參數
        prompt = (
            f"你需要使用工具 '{tool_name}' 來完成這個步驟：{step_desc}\n"
            f"已知的上下文資訊：\n"
            + "\n".join(state.get("step_results", []))
            + f"\n\n請提供工具的輸入參數（純文字）。"
        )
        tool_input = executor_llm.invoke(
            [{"role": "user", "content": prompt}]
        ).content

        # 執行工具
        tool_fn = TOOL_MAP[tool_name]
        result = tool_fn.invoke(tool_input)
        print(f"    工具輸出：{result}")
    else:
        # 不需要工具，用 LLM 處理
        context = "\n".join(state.get("step_results", []))
        prompt = (
            f"完成以下步驟：{step_desc}\n"
            f"已有的資訊：\n{context}\n"
            f"原始任務：{state['task']}"
        )
        result = executor_llm.invoke(
            [{"role": "user", "content": prompt}]
        ).content

    return {
        "step_results": [f"步驟 {idx + 1} 結果：{result}"],
        "current_step_index": idx + 1,
    }


# ---- 判斷是否繼續 ----
def should_continue(state: PlanExecuteState) -> str:
    """檢查是否還有步驟需要執行"""
    if state["current_step_index"] >= len(state["plan"]):
        return "summarize"
    return "executor"


# ---- 彙整節點 ----
def summarize(state: PlanExecuteState):
    """彙整所有步驟結果，生成最終回答"""
    context = "\n".join(state["step_results"])
    prompt = (
        f"根據以下執行結果，回答原始任務。用繁體中文回答。\n\n"
        f"原始任務：{state['task']}\n\n"
        f"執行結果：\n{context}"
    )
    response = executor_llm.invoke([{"role": "user", "content": prompt}])
    return {"final_answer": response.content}


# ---- 組裝圖 ----
workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("summarize", summarize)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_conditional_edges(
    "executor",
    should_continue,
    {
        "executor": "executor",      # 繼續下一步
        "summarize": "summarize",    # 所有步驟完成
    },
)
workflow.add_edge("summarize", END)

graph = workflow.compile()


# ---- 測試 ----
if __name__ == "__main__":
    print("=== Plan-and-Execute Agent ===\n")

    task = "台灣和日本的人口分別是多少？兩者的差距是多少倍？"
    print(f"任務：{task}\n")

    result = graph.invoke({"task": task, "step_results": []})
    print(f"\n{'='*50}")
    print(f"最終回答：{result['final_answer']}")
