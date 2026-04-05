# 15.1 範例：LangGraph + 非 LangChain SDK 的追蹤
# 使用 @traceable 裝飾器和 wrap_openai 包裝器
# 需要：pip install langgraph langsmith openai
# 需要：設定 LANGSMITH_API_KEY 和 OPENAI_API_KEY 環境變數

import os
import json
import operator
from typing import Annotated, Literal, TypedDict

import openai
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from langgraph.graph import StateGraph, START, END

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_xxxxx"


class State(TypedDict):
    messages: Annotated[list, operator.add]


# === 用 wrap_openai 包裝 OpenAI Client ===
# 這樣所有 OpenAI 呼叫都會自動追蹤
wrapped_client = wrap_openai(openai.Client())

tool_schema = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "搜尋網路資訊",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}


# === 用 @traceable 裝飾工具函數 ===
@traceable(run_type="tool", name="Search Tool")
def search(query: str) -> str:
    """搜尋工具 — 用 @traceable 裝飾後會自動追蹤"""
    if "天氣" in query:
        return "台北 28 度，多雲時晴。"
    return "找到了一些資訊。"


def call_tools(state: State) -> dict:
    """呼叫工具"""
    messages = state["messages"]
    tool_call = messages[-1]["tool_calls"][0]
    func_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    if func_name == "search":
        result = search(**arguments)
    else:
        result = f"Unknown tool: {func_name}"

    tool_message = {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "name": func_name,
        "content": result,
    }
    return {"messages": [tool_message]}


def should_continue(state: State) -> Literal["tools", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.get("tool_calls"):
        return "tools"
    return "__end__"


def call_model(state: State) -> dict:
    """呼叫 LLM — wrapped_client 會自動追蹤"""
    response = wrapped_client.chat.completions.create(
        messages=state["messages"],
        model="gpt-4o-mini",
        tools=[tool_schema],
    )
    raw_calls = response.choices[0].message.tool_calls
    tool_calls = [tc.to_dict() for tc in raw_calls] if raw_calls else []
    return {
        "messages": [
            {
                "role": "assistant",
                "content": response.choices[0].message.content,
                "tool_calls": tool_calls,
            }
        ]
    }


# === 建構 Graph ===
workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# === 執行 ===
result = app.invoke(
    {"messages": [{"role": "user", "content": "台北天氣如何？"}]}
)
print(result["messages"][-1]["content"])
