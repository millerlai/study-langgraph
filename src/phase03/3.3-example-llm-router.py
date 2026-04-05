# 3.3 範例：模擬 LLM 路由器（LLM 驅動的動態路由）
# 展示使用 Command 實現 LLM 語意分析路由（此範例為模擬，不需實際 LLM API key）。

from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command


# 1. 定義 State
class RouterState(TypedDict):
    user_input: str
    route: str
    result: str


# 2. 模擬 LLM 路由器（實際應用中替換為真正的 LLM 呼叫）
def simulate_llm_classification(user_input: str) -> str:
    """
    模擬 LLM 對使用者輸入的分類。

    在實際應用中，這裡會是：
        response = llm.invoke([
            SystemMessage("你是一個路由器。根據使用者輸入，回傳以下分類之一：research, code, write, chat"),
            HumanMessage(user_input)
        ])
        return response.content.strip()

    或使用 structured output：
        class RouteDecision(BaseModel):
            route: Literal["research", "code", "write", "chat"]
            reasoning: str

        response = llm.with_structured_output(RouteDecision).invoke(...)
        return response.route
    """
    input_lower = user_input.lower()

    # 模擬語意分析
    if any(w in input_lower for w in ["研究", "分析", "比較", "調查", "search", "research"]):
        return "research"
    elif any(w in input_lower for w in ["程式", "code", "寫程式", "python", "javascript", "debug"]):
        return "code"
    elif any(w in input_lower for w in ["寫", "文章", "草稿", "翻譯", "write", "draft"]):
        return "write"
    else:
        return "chat"


# 3. 定義 Node 函數
def llm_router(state: RouterState) -> Command[Literal["research_agent", "code_agent", "write_agent", "chat_agent"]]:
    """LLM 驅動的路由節點"""
    route = simulate_llm_classification(state["user_input"])
    print(f"[llm_router] 輸入='{state['user_input']}' -> 路由='{route}'")

    route_map = {
        "research": "research_agent",
        "code": "code_agent",
        "write": "write_agent",
        "chat": "chat_agent",
    }
    return Command(
        update={"route": route},
        goto=route_map[route],
    )


def research_agent(state: RouterState) -> dict:
    """研究 Agent"""
    result = f"[研究 Agent] 已完成對 '{state['user_input']}' 的研究分析，找到 5 篇相關論文。"
    print(f"[research_agent] 執行研究任務")
    return {"result": result}


def code_agent(state: RouterState) -> dict:
    """程式 Agent"""
    result = f"[程式 Agent] 已為 '{state['user_input']}' 產生程式碼解決方案。"
    print(f"[code_agent] 執行程式任務")
    return {"result": result}


def write_agent(state: RouterState) -> dict:
    """寫作 Agent"""
    result = f"[寫作 Agent] 已完成 '{state['user_input']}' 的文章草稿。"
    print(f"[write_agent] 執行寫作任務")
    return {"result": result}


def chat_agent(state: RouterState) -> dict:
    """聊天 Agent"""
    result = f"[聊天 Agent] 很高興和您聊天！關於 '{state['user_input']}'，讓我來回答。"
    print(f"[chat_agent] 執行聊天任務")
    return {"result": result}


# 4. 建構 Graph
builder = StateGraph(RouterState)
builder.add_node("llm_router", llm_router)
builder.add_node("research_agent", research_agent)
builder.add_node("code_agent", code_agent)
builder.add_node("write_agent", write_agent)
builder.add_node("chat_agent", chat_agent)

builder.add_edge(START, "llm_router")
# Command 的型別標註已告知 LangGraph 可能的路由目標，不需 add_conditional_edges
builder.add_edge("research_agent", END)
builder.add_edge("code_agent", END)
builder.add_edge("write_agent", END)
builder.add_edge("chat_agent", END)

graph = builder.compile()

# 5. 測試不同輸入
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
        "result": "",
    })
    print(f"路由: {result['route']}")
    print(f"結果: {result['result']}")
