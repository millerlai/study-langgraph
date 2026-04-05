# 6.1 範例：messages 模式搭配真實 LLM
# 展示即時顯示 LLM token 的完整使用模式（此處用模擬回應）
# 注意：實際使用需安裝 langchain-openai 或其他 provider，並設定 API key
"""
messages 模式搭配真實 LLM（需要安裝 langchain-openai 或其他 provider）
這裡展示的是完整的使用模式
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END, add_messages
from langchain_core.messages import AnyMessage, HumanMessage

# 假設已安裝並設定好 LLM：
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def chatbot(state: State) -> dict:
    # 實際使用時：
    # response = llm.invoke(state["messages"])
    # return {"messages": [response]}

    # 模擬回應
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="LangGraph 是一個 AI Agent 編排框架。")]}

builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile()

# 即時顯示 LLM token
print("AI: ", end="", flush=True)
for chunk in graph.stream(
    {"messages": [HumanMessage(content="什麼是 LangGraph？")]},
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] == "messages":
        msg_chunk = chunk["data"][0]
        # AIMessageChunk 表示 LLM 的一個 token
        if hasattr(msg_chunk, "content") and msg_chunk.content:
            print(msg_chunk.content, end="", flush=True)
print()  # 換行
# AI: LangGraph 是一個 AI Agent 編排框架。
