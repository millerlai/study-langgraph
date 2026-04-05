# 3.1 範例：線性序列（Sequential Steps）
# 展示使用 add_edge() 建立固定邊，節點按固定順序依次執行的文件處理管線。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 定義 State
class DocState(TypedDict):
    raw_text: str
    cleaned_text: str
    word_count: int
    summary: str


# 2. 定義 Node 函數
def clean_text(state: DocState) -> dict:
    """步驟一：清理文字（去除多餘空白）"""
    cleaned = " ".join(state["raw_text"].split())
    print(f"[clean_text] 清理完成：'{cleaned}'")
    return {"cleaned_text": cleaned}


def count_words(state: DocState) -> dict:
    """步驟二：計算字數"""
    count = len(state["cleaned_text"].split())
    print(f"[count_words] 字數：{count}")
    return {"word_count": count}


def generate_summary(state: DocState) -> dict:
    """步驟三：產生摘要"""
    text = state["cleaned_text"]
    summary = text[:50] + "..." if len(text) > 50 else text
    print(f"[generate_summary] 摘要：'{summary}'")
    return {"summary": summary}


# 3. 建構 Graph（線性序列）
builder = StateGraph(DocState)
builder.add_node("clean_text", clean_text)
builder.add_node("count_words", count_words)
builder.add_node("generate_summary", generate_summary)

# 線性連接：START → clean → count → summary → END
builder.add_edge(START, "clean_text")
builder.add_edge("clean_text", "count_words")
builder.add_edge("count_words", "generate_summary")
builder.add_edge("generate_summary", END)

graph = builder.compile()

# 4. 執行
result = graph.invoke({
    "raw_text": "  LangGraph   是一個   低階的    stateful   agent   編排框架  ",
    "cleaned_text": "",
    "word_count": 0,
    "summary": ""
})

print(f"\n最終結果：{result}")
