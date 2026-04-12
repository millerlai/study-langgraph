# 2.3 Private State — 進階範例：RAG Pipeline 的 Private State
# 展示多層 Private State 在 RAG（檢索增強生成）場景中的應用
# 不需要 API key

"""
進階範例：RAG（檢索增強生成）Pipeline
展示多層 Private State 在實際場景中的應用
"""
from typing import Annotated, TypedDict
from operator import add
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義多層 Schema
# ============================================================

# 公開 State（外部可見）
class PublicState(TypedDict):
    question: str                                    # 輸入：使用者問題
    answer: str                                      # 輸出：最終答案

# 檢索階段的私有輸出
class RetrievalOutput(TypedDict):
    raw_documents: list[str]                         # 原始文件（私有）
    relevance_scores: list[float]                    # 相關性分數（私有）

# 清洗階段的輸入
# 注意：實務上 CleaningInput 與 RetrievalOutput 結構相同，可共用同一個 class。
#       這裡分開定義純粹是為了展示「上游輸出 → 下游輸入」的資料流方向。
class CleaningInput(TypedDict):
    raw_documents: list[str]
    relevance_scores: list[float]

# 清洗階段的私有輸出
class CleaningOutput(TypedDict):
    cleaned_context: str                             # 清洗後的上下文（私有）

# 生成階段的輸入
class GenerationInput(TypedDict):
    question: str                                    # 從公開 State 讀取
    cleaned_context: str                             # 從私有 Channel 讀取

# ============================================================
# 2. 定義 Nodes
# ============================================================

def retrieve(state: PublicState) -> RetrievalOutput:
    """檢索節點：根據問題搜尋相關文件"""
    question = state["question"]
    # 模擬檢索
    docs = [
        f"文件A：{question}的基礎概念...",
        f"文件B：{question}的進階應用...",
        f"文件C：{question}的常見問題...",
    ]
    scores = [0.95, 0.82, 0.45]
    print(f"[Retrieve] 找到 {len(docs)} 篇文件")
    return {"raw_documents": docs, "relevance_scores": scores}

def clean(state: CleaningInput) -> CleaningOutput:
    """清洗節點：過濾低相關性文件，整理成上下文"""
    docs = state["raw_documents"]
    scores = state["relevance_scores"]

    # 只保留相關性 > 0.5 的文件
    relevant_docs = [
        doc for doc, score in zip(docs, scores) if score > 0.5
    ]
    context = " | ".join(relevant_docs)
    print(f"[Clean] 保留 {len(relevant_docs)}/{len(docs)} 篇文件")
    return {"cleaned_context": context}

def generate(state: GenerationInput) -> PublicState:
    """生成節點：根據問題和上下文生成答案"""
    question = state["question"]
    context = state["cleaned_context"]
    # 模擬 LLM 生成
    answer = f"根據 {context}，關於「{question}」的答案是..."
    print(f"[Generate] 生成答案")
    return {"answer": answer}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(PublicState)
builder.add_node("retrieve", retrieve)
builder.add_node("clean", clean)
builder.add_node("generate", generate)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "clean")
builder.add_edge("clean", "generate")
builder.add_edge("generate", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({
    "question": "LangGraph 的核心原語有哪些",
    "answer": "",
})

print(f"\n最終結果: {result}")
# 最終結果: {
#     "question": "LangGraph 的核心原語有哪些",
#     "answer": "根據 文件A... | 文件B...，關於「...」的答案是..."
# }
#
# 注意：raw_documents、relevance_scores、cleaned_context
#       都不會出現在最終結果中！
