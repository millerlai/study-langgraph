# 9.1 範例：多層子圖系統
# 展示兩層嵌套的子圖結構：子圖 A（內容提取）和子圖 B（品質檢查）
# 組合在父圖（文件處理管線）中。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 共享 State Schema
# ============================================================
class DocumentState(TypedDict):
    raw_input: str
    content: str
    logs: Annotated[list[str], lambda x, y: x + y]
    quality_passed: bool


# ============================================================
# 2. 子圖 A：內容提取
# ============================================================
def extract_content(state: DocumentState) -> dict:
    raw = state.get("raw_input", "")
    return {
        "content": f"已提取: {raw[:50]}",
        "logs": ["[提取] 從原始輸入中提取內容"]
    }

def clean_content(state: DocumentState) -> dict:
    return {
        "content": state["content"].strip(),
        "logs": ["[清理] 移除多餘空白和格式"]
    }

extraction_builder = StateGraph(DocumentState)
extraction_builder.add_node("extract", extract_content)
extraction_builder.add_node("clean", clean_content)
extraction_builder.add_edge(START, "extract")
extraction_builder.add_edge("extract", "clean")
extraction_builder.add_edge("clean", END)
extraction_subgraph = extraction_builder.compile()


# ============================================================
# 3. 子圖 B：品質檢查
# ============================================================
def check_grammar(state: DocumentState) -> dict:
    return {"logs": ["[文法] 文法檢查通過"]}

def check_facts(state: DocumentState) -> dict:
    content = state.get("content", "")
    passed = len(content) > 5
    return {
        "quality_passed": passed,
        "logs": [f"[事實] 事實查核{'通過' if passed else '未通過'}"]
    }

quality_builder = StateGraph(DocumentState)
quality_builder.add_node("grammar", check_grammar)
quality_builder.add_node("facts", check_facts)
quality_builder.add_edge(START, "grammar")
quality_builder.add_edge("grammar", "facts")
quality_builder.add_edge("facts", END)
quality_subgraph = quality_builder.compile()


# ============================================================
# 4. 父圖：文件處理管線
# ============================================================
def receive_document(state: DocumentState) -> dict:
    return {"logs": ["[接收] 收到文件，開始處理"]}

def output_result(state: DocumentState) -> dict:
    passed = state.get("quality_passed", False)
    status = "已通過品質檢查" if passed else "品質檢查未通過"
    return {"logs": [f"[輸出] {status}，處理完成"]}

parent_builder = StateGraph(DocumentState)
parent_builder.add_node("receive", receive_document)
parent_builder.add_node("extract", extraction_subgraph)   # 子圖 A
parent_builder.add_node("quality", quality_subgraph)       # 子圖 B
parent_builder.add_node("output", output_result)

parent_builder.add_edge(START, "receive")
parent_builder.add_edge("receive", "extract")
parent_builder.add_edge("extract", "quality")
parent_builder.add_edge("quality", "output")
parent_builder.add_edge("output", END)

pipeline = parent_builder.compile()


# ============================================================
# 5. 執行
# ============================================================
result = pipeline.invoke({
    "raw_input": "  LangGraph 子圖設計是模組化的關鍵技術...  ",
    "content": "",
    "logs": [],
    "quality_passed": False
})

print("=== 處理日誌 ===")
for log in result["logs"]:
    print(f"  {log}")
print(f"\n品質通過: {result['quality_passed']}")
print(f"最終內容: {result['content']}")
