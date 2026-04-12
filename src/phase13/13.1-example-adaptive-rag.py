# 13.1 範例：Adaptive RAG — 根據問題類型自動選擇檢索策略
# 需要設定 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai langchain-community

import os
import operator
from typing import TypedDict, Literal, Annotated
from langchain.chat_models import init_chat_model
from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

os.environ["OPENAI_API_KEY"] = "your-api-key"


# ---- State 定義 ----
class AdaptiveRAGState(TypedDict):
    question: str
    route: str
    context: str
    answer: str


# ---- 建立向量庫 ----
sample_docs = [
    Document(page_content="Python 3.12 於 2023 年 10 月發布，新增了型別參數語法。"),
    Document(page_content="LangGraph 使用 StateGraph 來定義有狀態的工作流。"),
    Document(page_content="Transformer 架構由 Vaswani 等人在 2017 年提出。"),
]
vectorstore = InMemoryVectorStore.from_documents(
    documents=sample_docs,
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()


# ---- LLM 初始化 ----
#llm = init_chat_model("gpt-4o-mini", temperature=0)  # Set OPENAI_API_KEY in environment variables, you could create API key at https://platform.openai.com/settings/organization/api-keys
llm = ChatAnthropic(model="claude-sonnet-4-5")  # Set ANTHROPIC_API_KEY in environment variables, you could create API key at https://platform.claude.com/settings/keys


# ---- 路由分類器 ----
class RouteDecision(BaseModel):
    """問題路由決策"""
    route: Literal["vector_search", "web_search", "direct_answer"] = Field(
        description="選擇處理路徑：vector_search 用於技術文件問題，"
        "web_search 用於需要最新資訊的問題，"
        "direct_answer 用於一般常識問題"
    )
    reasoning: str = Field(description="選擇此路徑的原因")


def route_question(state: AdaptiveRAGState):
    """根據問題內容決定檢索策略"""
    question = state["question"]
    prompt = (
        "你是一個問題路由器。分析以下問題，決定最佳處理方式：\n"
        "- vector_search：技術文件相關問題（如程式語言、框架等）\n"
        "- web_search：需要最新資訊的問題（如新聞、即時數據等）\n"
        "- direct_answer：一般常識或不需要外部資料的問題\n\n"
        f"問題：{question}"
    )
    decision = llm.with_structured_output(RouteDecision).invoke(
        [{"role": "user", "content": prompt}]
    )
    print(f"  [路由決策] {decision.route} — {decision.reasoning}")
    return {"route": decision.route}


def route_to_strategy(state: AdaptiveRAGState) -> str:
    """條件邊：根據路由決策導向對應節點"""
    return state["route"]


# ---- 三種檢索策略 ----
def vector_search(state: AdaptiveRAGState):
    """向量檢索策略"""
    docs = retriever.invoke(state["question"])
    context = "\n".join([doc.page_content for doc in docs])
    print(f"  [向量檢索] 找到 {len(docs)} 筆文件")
    return {"context": context}


def web_search(state: AdaptiveRAGState):
    """網路搜尋策略（模擬）"""
    # 實際專案中可使用 Tavily、SerpAPI 等搜尋工具
    simulated_result = f"[模擬網路搜尋結果] 關於「{state['question']}」的最新資訊..."
    print(f"  [網路搜尋] 已執行搜尋")
    return {"context": simulated_result}


def direct_answer(state: AdaptiveRAGState):
    """直接回答，不需要檢索"""
    print(f"  [直接回答] 不需要外部檢索")
    return {"context": "（無需外部參考資料）"}


# ---- 生成節點 ----
def generate(state: AdaptiveRAGState):
    """根據檢索到的上下文生成最終回答"""
    prompt = (
        "根據以下參考內容回答問題。用繁體中文回答，保持簡潔。\n\n"
        f"問題：{state['question']}\n"
        f"參考內容：{state['context']}"
    )
    response = llm.invoke([{"role": "user", "content": prompt}])
    return {"answer": response.content}


# ---- 組裝圖 ----
workflow = StateGraph(AdaptiveRAGState)

workflow.add_node("route_question", route_question)
workflow.add_node("vector_search", vector_search)
workflow.add_node("web_search", web_search)
workflow.add_node("direct_answer", direct_answer)
workflow.add_node("generate", generate)

workflow.add_edge(START, "route_question")
workflow.add_conditional_edges(
    "route_question",
    route_to_strategy,
    {
        "vector_search": "vector_search",
        "web_search": "web_search",
        "direct_answer": "direct_answer",
    },
)
workflow.add_edge("vector_search", "generate")
workflow.add_edge("web_search", "generate")
workflow.add_edge("direct_answer", "generate")
workflow.add_edge("generate", END)

graph = workflow.compile()


# ---- 測試 ----
if __name__ == "__main__":
    test_questions = [
        "LangGraph 的 StateGraph 怎麼用？",
        "今天台積電的股價是多少？",
        "太陽從哪個方向升起？",
    ]

    for q in test_questions:
        print(f"\n{'='*50}")
        print(f"問題：{q}")
        result = graph.invoke({"question": q})
        print(f"回答：{result['answer']}")
