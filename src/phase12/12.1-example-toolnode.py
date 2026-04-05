# 12.1 範例：ToolNode — 在 LangGraph 圖中執行工具
# 示範 ToolNode 搭配 tools_condition 的基本用法

from langchain.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import HumanMessage, AIMessage

# ============================================================
# 1. 定義工具
# ============================================================
@tool
def search(query: str) -> str:
    """搜尋資訊。"""
    results = {
        "LangGraph": "LangGraph 是一個用於建構有狀態 AI Agent 的框架。",
        "Python": "Python 是一種高階程式語言。"
    }
    return results.get(query, f"找不到關於 '{query}' 的結果")

@tool
def calculator(expression: str) -> str:
    """計算數學表達式。"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"計算錯誤: {e}"

# ============================================================
# 2. 建立 ToolNode
# ============================================================
tools = [search, calculator]
tool_node = ToolNode(tools)

# ============================================================
# 3. 模擬 LLM 節點
# ============================================================
def call_llm(state: MessagesState):
    """模擬 LLM 回應（實際應用中接 ChatModel）"""
    last_msg = state["messages"][-1]

    if isinstance(last_msg, HumanMessage):
        # 模擬 LLM 決定呼叫 search 工具
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{
                        "id": "call_001",
                        "name": "search",
                        "args": {"query": "LangGraph"}
                    }]
                )
            ]
        }
    else:
        # 工具結果回來後，生成最終回覆
        return {
            "messages": [
                AIMessage(content="根據搜尋結果：LangGraph 是一個用於建構有狀態 AI Agent 的框架。")
            ]
        }

# ============================================================
# 4. 建立圖
# ============================================================
builder = StateGraph(MessagesState)
builder.add_node("llm", call_llm)
builder.add_node("tools", tool_node)

builder.add_edge(START, "llm")
builder.add_conditional_edges("llm", tools_condition)  # 有 tool_calls → "tools"，否則 → END
builder.add_edge("tools", "llm")

graph = builder.compile()

# ============================================================
# 5. 執行
# ============================================================
result = graph.invoke({
    "messages": [HumanMessage(content="什麼是 LangGraph?")]
})

for msg in result["messages"]:
    role = msg.__class__.__name__
    content = msg.content or f"[tool_calls: {msg.tool_calls}]" if hasattr(msg, 'tool_calls') and msg.tool_calls else msg.content
    print(f"{role}: {content}")
# 輸出:
# HumanMessage: 什麼是 LangGraph?
# AIMessage: [tool_calls: [{'id': 'call_001', 'name': 'search', 'args': {'query': 'LangGraph'}}]]
# ToolMessage: LangGraph 是一個用於建構有狀態 AI Agent 的框架。
# AIMessage: 根據搜尋結果：LangGraph 是一個用於建構有狀態 AI Agent 的框架。
