# 13.2 範例：動態重新規劃（Re-Planning）的 Plan-and-Execute Agent
# 可在執行過程中根據結果調整後續計畫
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai

import os
from typing import TypedDict, Annotated, Literal
import operator
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END

os.environ["OPENAI_API_KEY"] = "your-api-key"


# ---- State 定義 ----
class ReplanState(TypedDict):
    task: str
    plan: list[str]                                     # 步驟描述列表
    completed_steps: Annotated[list[str], operator.add]  # 已完成步驟及結果
    current_step: str                                    # 當前步驟
    final_answer: str


# ---- 工具 ----
@tool
def web_search(query: str) -> str:
    """在網路上搜尋資訊（模擬）"""
    simulated_results = {
        "python 3.13": "Python 3.13 新增 free-threaded 模式和改進的錯誤訊息。",
        "langgraph": "LangGraph 是 LangChain 生態的 Agent 框架，用於建構有狀態工作流。",
        "react": "React 是 Meta 開發的前端 JavaScript 框架。",
    }
    for key, val in simulated_results.items():
        if key.lower() in query.lower():
            return val
    return f"搜尋 '{query}' 的結果：[未找到精確結果]"


@tool
def code_executor(code: str) -> str:
    """執行 Python 程式碼片段（模擬，僅支援安全表達式）"""
    try:
        result = eval(code, {"__builtins__": {}})
        return f"執行結果：{result}"
    except Exception as e:
        return f"執行錯誤：{str(e)}"


TOOLS = [web_search, code_executor]
TOOL_MAP = {t.name: t for t in TOOLS}

# ---- LLM ----
planner_llm = init_chat_model("gpt-4o-mini", temperature=0)
executor_llm = init_chat_model("gpt-4o-mini", temperature=0)


# ---- 規劃器 ----
class PlanOutput(BaseModel):
    steps: list[str] = Field(description="按順序的步驟描述列表")


def planner(state: ReplanState):
    """制定初始計畫"""
    task = state["task"]
    tool_info = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS])

    prompt = (
        "你是任務規劃專家。制定一個簡潔的執行計畫。\n"
        "每個步驟應該清楚、具體、可執行。\n"
        f"可用工具：\n{tool_info}\n\n"
        f"任務：{task}\n\n"
        "輸出 3-5 個步驟的計畫。"
    )

    plan = planner_llm.with_structured_output(PlanOutput).invoke(
        [{"role": "user", "content": prompt}]
    )
    print("  [規劃器] 初始計畫：")
    for i, step in enumerate(plan.steps, 1):
        print(f"    {i}. {step}")

    return {
        "plan": plan.steps,
        "current_step": plan.steps[0] if plan.steps else "",
    }


# ---- 執行器 ----
def executor(state: ReplanState):
    """執行當前步驟"""
    step = state["current_step"]
    completed = state.get("completed_steps", [])

    print(f"\n  [執行器] 執行：{step}")

    context = "\n".join(completed) if completed else "（尚無前置結果）"
    tool_info = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS])

    prompt = (
        f"完成以下步驟：{step}\n\n"
        f"可用工具：\n{tool_info}\n\n"
        f"先前結果：\n{context}\n\n"
        f"如果需要使用工具，請指明工具名稱和輸入。"
        f"如果不需要工具，直接給出結果。"
    )

    response = executor_llm.invoke([{"role": "user", "content": prompt}])
    result_text = response.content

    # 檢查是否需要呼叫工具（簡單的文字解析）
    for tool_name, tool_fn in TOOL_MAP.items():
        if tool_name in result_text.lower():
            # 嘗試提取工具輸入並執行
            tool_response = tool_fn.invoke(step)
            result_text += f"\n工具回應：{tool_response}"
            break

    print(f"    結果：{result_text[:150]}")

    return {
        "completed_steps": [f"[{step}] -> {result_text}"],
    }


# ---- 重新規劃器 ----
class ReplanDecision(BaseModel):
    action: Literal["continue", "replan", "finish"] = Field(
        description="continue=按原計畫繼續, replan=調整計畫, finish=任務完成"
    )
    updated_steps: list[str] = Field(
        default=[],
        description="若 action=replan，提供新的剩餘步驟"
    )
    reasoning: str = Field(description="決策理由")


def replanner(state: ReplanState):
    """評估進度，決定是否需要調整計畫"""
    task = state["task"]
    plan = state["plan"]
    completed = state.get("completed_steps", [])

    # 找到下一個待執行步驟的索引
    completed_count = len(completed)

    prompt = (
        "你是任務進度評估者。根據已完成的步驟和原計畫，決定下一步行動。\n\n"
        f"原始任務：{task}\n\n"
        f"原計畫：\n" + "\n".join([f"  {i+1}. {s}" for i, s in enumerate(plan)]) + "\n\n"
        f"已完成的步驟及結果：\n" + "\n".join(completed) + "\n\n"
        "選擇行動：\n"
        "- continue：按原計畫執行下一步\n"
        "- replan：根據目前結果調整後續步驟\n"
        "- finish：已有足夠資訊，可以給出最終回答\n"
    )

    decision = planner_llm.with_structured_output(ReplanDecision).invoke(
        [{"role": "user", "content": prompt}]
    )

    print(f"\n  [重規劃器] 決策：{decision.action} — {decision.reasoning}")

    if decision.action == "finish":
        # 生成最終回答
        answer_prompt = (
            f"根據以下資訊回答任務。用繁體中文回答。\n\n"
            f"任務：{task}\n\n"
            f"收集到的資訊：\n" + "\n".join(completed)
        )
        response = executor_llm.invoke([{"role": "user", "content": answer_prompt}])
        return {"final_answer": response.content}

    elif decision.action == "replan":
        # 更新計畫
        new_plan = decision.updated_steps
        print("  [重規劃器] 新計畫：")
        for i, step in enumerate(new_plan, 1):
            print(f"    {i}. {step}")
        return {
            "plan": new_plan,
            "current_step": new_plan[0] if new_plan else "",
        }

    else:  # continue
        # 按原計畫繼續
        remaining = plan[completed_count:]
        if remaining:
            return {"current_step": remaining[0]}
        else:
            # 所有步驟已完成
            answer_prompt = (
                f"根據以下資訊回答任務。用繁體中文回答。\n\n"
                f"任務：{task}\n\n"
                f"收集到的資訊：\n" + "\n".join(completed)
            )
            response = executor_llm.invoke(
                [{"role": "user", "content": answer_prompt}]
            )
            return {"final_answer": response.content}


def should_end(state: ReplanState) -> Literal["executor", "__end__"]:
    """根據是否有最終回答決定是否結束"""
    if state.get("final_answer"):
        return "__end__"
    return "executor"


# ---- 組裝圖 ----
workflow = StateGraph(ReplanState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("replanner", replanner)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "replanner")
workflow.add_conditional_edges(
    "replanner",
    should_end,
    {
        "executor": "executor",
        "__end__": END,
    },
)

graph = workflow.compile()


# ---- 測試 ----
if __name__ == "__main__":
    print("=== 動態重新規劃 Agent ===\n")

    task = "請比較 Python 3.13 和 LangGraph 各自的主要特色，並總結它們之間有什麼關聯。"
    print(f"任務：{task}\n")

    result = graph.invoke({
        "task": task,
        "plan": [],
        "completed_steps": [],
        "current_step": "",
        "final_answer": "",
    })

    print(f"\n{'='*60}")
    print(f"最終回答：\n{result['final_answer']}")
