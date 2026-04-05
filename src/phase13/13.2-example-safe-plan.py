# 13.2 範例：帶有迭代次數限制的 Plan-and-Execute Agent
# 生產環境中防止無限迴圈的安全保護版本
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai

import os
from typing import TypedDict, Annotated, Literal
import operator
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

os.environ["OPENAI_API_KEY"] = "your-api-key"

MAX_ITERATIONS = 10  # 最大迭代次數


class SafePlanState(TypedDict):
    task: str
    plan: list[str]
    completed_steps: Annotated[list[str], operator.add]
    current_step: str
    iteration_count: int
    final_answer: str


llm = init_chat_model("gpt-4o-mini", temperature=0)


class PlanOutput(BaseModel):
    steps: list[str]


def planner(state: SafePlanState):
    prompt = f"為以下任務制定 3-5 步簡潔計畫：\n{state['task']}"
    plan = llm.with_structured_output(PlanOutput).invoke(
        [{"role": "user", "content": prompt}]
    )
    return {
        "plan": plan.steps,
        "current_step": plan.steps[0] if plan.steps else "",
        "iteration_count": 0,
    }


def executor(state: SafePlanState):
    step = state["current_step"]
    context = "\n".join(state.get("completed_steps", []))
    prompt = f"執行步驟：{step}\n已有資訊：\n{context}"
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {
        "completed_steps": [f"[{step}] -> {response.content}"],
        "iteration_count": state["iteration_count"] + 1,
    }


def check_progress(state: SafePlanState) -> Literal["executor", "finish"]:
    """檢查是否繼續，包含安全保護"""
    # 安全閥：超過最大迭代次數強制結束
    if state["iteration_count"] >= MAX_ITERATIONS:
        print(f"  [安全] 達到最大迭代次數 {MAX_ITERATIONS}，強制結束")
        return "finish"

    completed_count = len(state.get("completed_steps", []))
    if completed_count >= len(state["plan"]):
        return "finish"

    # 設定下一步
    return "executor"


def update_next_step(state: SafePlanState):
    """更新 current_step 為下一個待執行步驟"""
    completed_count = len(state.get("completed_steps", []))
    plan = state["plan"]
    if completed_count < len(plan):
        return {"current_step": plan[completed_count]}
    return {}


def finish(state: SafePlanState):
    context = "\n".join(state.get("completed_steps", []))
    prompt = f"根據以下結果回答任務（繁��中文）：\n任務：{state['task']}\n結果：\n{context}"
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"final_answer": response.content}


# ---- 組裝 ----
workflow = StateGraph(SafePlanState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("update_next_step", update_next_step)
workflow.add_node("finish", finish)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "update_next_step")
workflow.add_conditional_edges(
    "update_next_step",
    check_progress,
    {"executor": "executor", "finish": "finish"},
)
workflow.add_edge("finish", END)

graph = workflow.compile()


if __name__ == "__main__":
    result = graph.invoke({
        "task": "列出 LangGraph 的三個核心概念並簡單解釋",
        "plan": [],
        "completed_steps": [],
        "current_step": "",
        "iteration_count": 0,
        "final_answer": "",
    })
    print(f"回答：{result['final_answer']}")
