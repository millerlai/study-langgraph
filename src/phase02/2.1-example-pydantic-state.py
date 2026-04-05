# 2.1 State Schema 設計 — 使用 Pydantic Model 定義 State 的完整範例
# 展示 Pydantic 的執行時驗證能力
# 不需要 API key

"""
使用 Pydantic Model 定義 State 的完整範例
展示執行時驗證能力
"""
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義 State Schema（含驗證規則）
# ============================================================
class ReviewState(BaseModel):
    content: str = Field(description="要審核的內容")
    reviewer: str = Field(default="auto", description="審核者名稱")
    score: int = Field(default=0, ge=0, le=100, description="評分 0~100")
    approved: bool = Field(default=False, description="是否通過審核")
    comments: list[str] = Field(default_factory=list, description="審核意見")

# ============================================================
# 2. 定義 Nodes
# ============================================================
def review(state: ReviewState) -> dict:
    """自動審核節點"""
    content = state.content
    # 模擬評分邏輯
    score = min(len(content) * 5, 100)  # 越長分越高（簡化邏輯）
    return {
        "score": score,
        "approved": score >= 60,
        "comments": [f"自動審核完成，評分：{score}"],
    }

def finalize(state: ReviewState) -> dict:
    """完成節點"""
    status = "通過" if state.approved else "未通過"
    return {
        "comments": state.comments + [f"最終結果：{status}"],
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(ReviewState)
builder.add_node("review", review)
builder.add_node("finalize", finalize)
builder.add_edge(START, "review")
builder.add_edge("review", "finalize")
builder.add_edge("finalize", END)

graph = builder.compile()

# ============================================================
# 4. 執行——正常情況
# ============================================================
result = graph.invoke({"content": "這是一篇很棒的技術文章，內容豐富。"})
print(result)
# score: 80, approved: True

# ============================================================
# 5. 執行——驗證錯誤（Pydantic 會攔截）
# ============================================================
try:
    # score 超出範圍 0~100，Pydantic 會拋出 ValidationError
    result = graph.invoke({"content": "test", "score": 999})
except Exception as e:
    print(f"驗證錯誤：{e}")
