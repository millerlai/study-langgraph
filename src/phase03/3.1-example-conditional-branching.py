# 3.1 範例：條件分支（Conditional Branching）
# 展示使用 add_conditional_edges() 搭配路由函數，根據情緒分數動態決定下一步。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義 State
class SentimentState(TypedDict):
    text: str
    score: float
    sentiment: str
    response: str


# 2. 定義 Node 函數
def analyze(state: SentimentState) -> dict:
    """分析文字情緒（模擬：根據關鍵字判斷）"""
    text = state["text"].lower()
    if any(w in text for w in ["好", "棒", "讚", "開心", "great"]):
        score = 0.8
    elif any(w in text for w in ["差", "爛", "糟", "難過", "bad"]):
        score = -0.8
    else:
        score = 0.0
    print(f"[analyze] 文字='{state['text']}', 分數={score}")
    return {"score": score}


def positive_handler(state: SentimentState) -> dict:
    """處理正面情緒"""
    print("[positive_handler] 正面情緒處理")
    return {"sentiment": "positive", "response": "感謝您的正面回饋！"}


def neutral_handler(state: SentimentState) -> dict:
    """處理中性情緒"""
    print("[neutral_handler] 中性情緒處理")
    return {"sentiment": "neutral", "response": "感謝您的回饋，我們會持續改進。"}


def negative_handler(state: SentimentState) -> dict:
    """處理負面情緒"""
    print("[negative_handler] 負面情緒處理")
    return {"sentiment": "negative", "response": "很抱歉造成不好的體驗，我們會改善！"}


# 3. 定義路由函數
def route_by_sentiment(state: SentimentState) -> str:
    """根據情緒分數決定下一個節點"""
    score = state["score"]
    if score > 0.3:
        return "positive_handler"
    elif score < -0.3:
        return "negative_handler"
    else:
        return "neutral_handler"


# 4. 建構 Graph
builder = StateGraph(SentimentState)
builder.add_node("analyze", analyze)
builder.add_node("positive_handler", positive_handler)
builder.add_node("neutral_handler", neutral_handler)
builder.add_node("negative_handler", negative_handler)

builder.add_edge(START, "analyze")

# 條件分支：analyze 執行完後，根據路由函數決定下一步
builder.add_conditional_edges(
    "analyze",
    route_by_sentiment,
    ["positive_handler", "neutral_handler", "negative_handler"]
)

# 三個分支都導向 END
builder.add_edge("positive_handler", END)
builder.add_edge("neutral_handler", END)
builder.add_edge("negative_handler", END)

graph = builder.compile()

# 5. 測試不同情緒
print("=== 測試正面 ===")
r1 = graph.invoke({"text": "這個產品真的很棒！", "score": 0.0, "sentiment": "", "response": ""})
print(f"回應：{r1['response']}\n")

print("=== 測試負面 ===")
r2 = graph.invoke({"text": "服務太差了", "score": 0.0, "sentiment": "", "response": ""})
print(f"回應：{r2['response']}\n")

print("=== 測試中性 ===")
r3 = graph.invoke({"text": "今天天氣不錯", "score": 0.0, "sentiment": "", "response": ""})
print(f"回應：{r3['response']}")
