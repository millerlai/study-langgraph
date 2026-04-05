# 13.1 範例：Self-RAG — 帶有文件評分與問題重寫的 RAG Agent
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai langchain-community

import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.messages import HumanMessage, convert_to_messages
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

os.environ["OPENAI_API_KEY"] = "your-api-key"


# ---- 向量庫準備 ----
sample_docs = [
    Document(page_content="LangGraph 的 Reducer 機制決定了多個節點寫入同一個欄位時如何合併值。"),
    Document(page_content="常見的 Reducer 包括 operator.add（累加列表）和自定義函數。"),
    Document(page_content="LangGraph 支援 Human-in-the-loop，使用 interrupt() 暫停執行等待人類審核。"),
    Document(page_content="Checkpointer 可以將圖的狀態持久化到 SQLite、PostgreSQL 等儲存後端。"),
]

vectorstore = InMemoryVectorStore.from_documents(
    documents=sample_docs,
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()


# ---- 檢索工具 ----
@tool
def retrieve_docs(query: str) -> str:
    """搜尋 LangGraph 技術文件，回傳相關內容。"""
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])


# ---- LLM ----
llm = init_chat_model("gpt-4o-mini", temperature=0)


# ---- 節點定義 ----
def generate_query_or_respond(state: MessagesState):
    """LLM 決定要檢索還是直接回答"""
    response = llm.bind_tools([retrieve_docs]).invoke(state["messages"])
    return {"messages": [response]}


# ---- 文件評分（Self-RAG 的核心）----
class GradeDocuments(BaseModel):
    """文件相關性評分"""
    binary_score: Literal["yes", "no"] = Field(
        description="文件是否與問題相關：'yes' 或 'no'"
    )


GRADE_PROMPT = (
    "你是一個文件相關性評分員。\n"
    "以下是檢索到的文件內容：\n\n{context}\n\n"
    "以下是使用者的問題：{question}\n\n"
    "如果文件包含與問題語意相關的關鍵字或概念，判斷為相關。\n"
    "請給出二元評分：'yes'（相關）或 'no'（不相關）。"
)


def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:
    """評估檢索到的文件是否與問題相關"""
    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = GRADE_PROMPT.format(question=question, context=context)
    grader = llm.with_structured_output(GradeDocuments)
    result = grader.invoke([{"role": "user", "content": prompt}])

    if result.binary_score == "yes":
        print("  [評分] 文件相關 -> 生成回答")
        return "generate_answer"
    else:
        print("  [評分] 文件不相關 -> 重寫問題")
        return "rewrite_question"


# ---- 問題重寫 ----
REWRITE_PROMPT = (
    "分析以下問題的語意意圖，重新表述為更精確的搜尋查詢。\n"
    "原始問題：\n-------\n{question}\n-------\n"
    "請輸出改進後的問題："
)


def rewrite_question(state: MessagesState):
    """重寫問題以獲得更好的檢索結果"""
    question = state["messages"][0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = llm.invoke([{"role": "user", "content": prompt}])
    print(f"  [重寫] {question} -> {response.content}")
    return {"messages": [HumanMessage(content=response.content)]}


# ---- 生成回答 ----
GENERATE_PROMPT = (
    "你是問答助手。根據以下參考內容回答問題。"
    "如果不確定，請說不知道。用繁體中文回答，最多三句話。\n"
    "問題：{question}\n"
    "參考內容：{context}"
)


def generate_answer(state: MessagesState):
    """根據檢索結果生成回答"""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


# ---- 組裝圖 ----
workflow = StateGraph(MessagesState)

workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([retrieve_docs]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)

# 邊
workflow.add_edge(START, "generate_query_or_respond")
workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition,
    {"tools": "retrieve", END: END},
)
# 核心：檢索後評分，決定下一步
workflow.add_conditional_edges(
    "retrieve",
    grade_documents,
    {
        "generate_answer": "generate_answer",
        "rewrite_question": "rewrite_question",
    },
)
workflow.add_edge("generate_answer", END)
# 重寫後回到 LLM 重新決策
workflow.add_edge("rewrite_question", "generate_query_or_respond")

graph = workflow.compile()


# ---- 測試 ----
if __name__ == "__main__":
    print("=== Self-RAG 測試 ===\n")

    # 測試：技術問題
    print("問題：LangGraph 的 Reducer 是什麼？")
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "LangGraph 的 Reducer 是什麼？"}]}
    ):
        for node, update in chunk.items():
            msg = update["messages"][-1]
            if hasattr(msg, "content") and msg.content:
                print(f"  [{node}] {msg.content[:120]}")

    print("\n問題：什麼是微積分的基本定理？")
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "什麼是微積分的基本定理？"}]}
    ):
        for node, update in chunk.items():
            msg = update["messages"][-1]
            if hasattr(msg, "content") and msg.content:
                print(f"  [{node}] {msg.content[:120]}")
