# 2.1 State Schema 設計 — Input / Output Schema 分離設計
# 展示如何控制圖的輸入和輸出介面，隱藏內部欄位
# 不需要 API key

"""
Input / Output Schema 分離設計
展示如何控制圖的輸入和輸出介面
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義三層 Schema
# ============================================================

# 外部輸入只需要這些
class InputState(TypedDict):
    question: str               # 使用者問題

# 外部輸出只回傳這些
class OutputState(TypedDict):
    answer: str                 # 最終答案
    confidence: float           # 信心分數

# 內部完整 State（包含所有欄位）
class OverallState(InputState, OutputState):
    # 繼承自 InputState: question
    # 繼承自 OutputState: answer, confidence
    retrieved_docs: list[str]   # 內部用：檢索到的文件
    reasoning: str              # 內部用：推理過程
    attempt_count: int          # 內部用：嘗試次數

# ============================================================
# 2. 定義 Nodes
# ============================================================
def retrieve(state: InputState) -> dict:
    """檢索節點：根據問題搜尋相關文件"""
    question = state["question"]
    # 模擬文件檢索
    docs = [
        f"文件1：關於 {question} 的背景資料...",
        f"文件2：{question} 的最新研究...",
    ]
    return {
        "retrieved_docs": docs,
        "attempt_count": 1,
    }

def reason(state: OverallState) -> dict:
    """推理節點：根據檢索結果進行推理"""
    docs = state["retrieved_docs"]
    question = state["question"]
    reasoning = f"基於 {len(docs)} 篇文件，分析問題「{question}」..."
    return {"reasoning": reasoning}

def answer(state: OverallState) -> dict:
    """回答節點：生成最終答案"""
    return {
        "answer": f"根據分析：{state['reasoning']}，結論是...",
        "confidence": 0.85,
    }

# ============================================================
# 3. 建構 Graph（指定 input/output schema）
# ============================================================
builder = StateGraph(
    OverallState,                  # 內部完整 Schema
    input_schema=InputState,       # 外部輸入限制
    output_schema=OutputState,     # 外部輸出限制
)

builder.add_node("retrieve", retrieve)
builder.add_node("reason", reason)
builder.add_node("answer", answer)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "reason")
builder.add_edge("reason", "answer")
builder.add_edge("answer", END)

graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================

# 輸入：只需傳 InputState 的欄位
result = graph.invoke({"question": "LangGraph 是什麼？"})

print(result)
# 輸出只包含 OutputState 的欄位：
# {"answer": "根據分析：...，結論是...", "confidence": 0.85}
#
# 注意：retrieved_docs、reasoning、attempt_count 不會出現在輸出中！
