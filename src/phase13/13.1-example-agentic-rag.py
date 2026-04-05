# 13.1 範例：Agentic RAG — 讓 LLM 自行決定是否檢索
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai langchain-community langchain-text-splitters

import os
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

os.environ["OPENAI_API_KEY"] = "your-api-key"

# ---- 第一步：準備文件並建立向量索引 ----
# 這裡用簡單的範例文件代替真實資料
sample_docs = [
    Document(
        page_content="LangGraph 是一個用於建構有狀態 AI Agent 的框架，"
        "它基於 LangChain 之上，提供了圖狀工作流的原語。",
        metadata={"source": "langgraph-intro"},
    ),
    Document(
        page_content="LangGraph 的核心概念包括 StateGraph、Node、Edge。"
        "StateGraph 定義了整個工作流的結構，Node 是執行邏輯的單元，"
        "Edge 則定義了 Node 之間的連接。",
        metadata={"source": "langgraph-concepts"},
    ),
    Document(
        page_content="Checkpointer 是 LangGraph 的持久化機制，"
        "它可以在每個超級步驟後保存圖的狀態，"
        "讓你可以暫停、恢復甚至回溯執行。",
        metadata={"source": "langgraph-checkpointer"},
    ),
    Document(
        page_content="Human-in-the-loop 模式讓人類可以在 Agent 執行過程中"
        "介入審核或修改，常用 interrupt() 函數實現。",
        metadata={"source": "langgraph-hitl"},
    ),
]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
doc_splits = text_splitter.split_documents(sample_docs)

vectorstore = InMemoryVectorStore.from_documents(
    documents=doc_splits,
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()


# ---- 第二步：定義檢索工具 ----
@tool
def search_langgraph_docs(query: str) -> str:
    """搜尋 LangGraph 相關技術文件，回傳最相關的內容片段。"""
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])


# ---- 第三步：定義節點 ----
llm = init_chat_model("gpt-4o-mini", temperature=0)


def generate_query_or_respond(state: MessagesState):
    """LLM 決定：使用檢索工具 or 直接回答"""
    response = llm.bind_tools([search_langgraph_docs]).invoke(state["messages"])
    return {"messages": [response]}


def generate_answer(state: MessagesState):
    """根據檢索結果生成最終回答"""
    question = state["messages"][0].content
    # 最後一條訊息是 ToolMessage（檢索結果）
    context = state["messages"][-1].content

    prompt = (
        "你是一個技術文件問答助手。根據以下檢索到的內容回答問題。"
        "如果內容中沒有答案，請說你不確定。用繁體中文回答。\n"
        f"問題：{question}\n"
        f"參考內容：{context}"
    )
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}


# ---- 第四步：組裝圖 ----
workflow = StateGraph(MessagesState)

workflow.add_node(generate_query_or_respond)
workflow.add_node("retrieve", ToolNode([search_langgraph_docs]))
workflow.add_node(generate_answer)

workflow.add_edge(START, "generate_query_or_respond")
workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition,                    # 有 tool_calls -> "tools", 沒有 -> END
    {"tools": "retrieve", END: END},
)
workflow.add_edge("retrieve", "generate_answer")
workflow.add_edge("generate_answer", END)

graph = workflow.compile()


# ---- 第五步：測試 ----
if __name__ == "__main__":
    # 測試 1：需要檢索的問題
    print("=== 測試 1：技術問題（需檢索）===")
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "LangGraph 的 Checkpointer 是什麼？"}]}
    ):
        for node, update in chunk.items():
            print(f"[{node}]", update["messages"][-1].content[:100])

    print("\n=== 測試 2：一般問題（直接回答）===")
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "你好，今天天氣如何？"}]}
    ):
        for node, update in chunk.items():
            print(f"[{node}]", update["messages"][-1].content[:100])
