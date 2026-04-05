# 9.1 範例：父子圖使用不同 State Schema
# 子圖「翻譯模組」有自己的私有 State，父圖「文件處理管線」透過包裝函式呼叫子圖。

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 定義父圖的 State Schema
# ============================================================
class ParentState(TypedDict):
    original_text: str          # 原始文本
    source_lang: str            # 來源語言
    target_lang: str            # 目標語言
    translated_text: str        # 翻譯結果
    quality_score: float        # 品質分數


# ============================================================
# 2. 定義子圖的 State Schema（私有）
# ============================================================
class TranslationState(TypedDict):
    input_text: str             # 輸入文本
    lang_pair: str              # 語言對（如 "zh->en"）
    intermediate: str           # 中間翻譯結果
    final_output: str           # 最終翻譯輸出
    confidence: float           # 翻譯信心度


# ============================================================
# 3. 定義子圖的節點
# ============================================================
def initial_translate(state: TranslationState) -> dict:
    """初步翻譯"""
    text = state["input_text"]
    lang = state["lang_pair"]
    return {
        "intermediate": f"[初步翻譯 {lang}] {text}",
        "confidence": 0.75
    }

def refine_translation(state: TranslationState) -> dict:
    """精煉翻譯"""
    return {
        "final_output": f"[精煉] {state['intermediate']}",
        "confidence": 0.92
    }

# 建立並編譯子圖
translation_builder = StateGraph(TranslationState)
translation_builder.add_node("initial", initial_translate)
translation_builder.add_node("refine", refine_translation)
translation_builder.add_edge(START, "initial")
translation_builder.add_edge("initial", "refine")
translation_builder.add_edge("refine", END)
translation_subgraph = translation_builder.compile()


# ============================================================
# 4. 定義包裝函式（State 轉換）
# ============================================================
def call_translation_subgraph(state: ParentState) -> dict:
    """
    包裝函式：負責父圖 State <-> 子圖 State 的轉換。

    1. 從父圖 State 提取資料，構建子圖 State
    2. 呼叫子圖
    3. 從子圖結果提取資料，寫回父圖 State
    """
    # 父 State -> 子 State
    sub_input = {
        "input_text": state["original_text"],
        "lang_pair": f"{state['source_lang']}->{state['target_lang']}",
        "intermediate": "",
        "final_output": "",
        "confidence": 0.0
    }

    # 呼叫子圖
    sub_result = translation_subgraph.invoke(sub_input)

    # 子 State -> 父 State
    return {
        "translated_text": sub_result["final_output"],
        "quality_score": sub_result["confidence"]
    }


# ============================================================
# 5. 定義父圖的其他節點
# ============================================================
def preprocess(state: ParentState) -> dict:
    """前處理：清理文本"""
    cleaned = state["original_text"].strip()
    return {"original_text": cleaned}

def postprocess(state: ParentState) -> dict:
    """後處理：格式化輸出"""
    score = state.get("quality_score", 0)
    quality = "高" if score > 0.85 else "中" if score > 0.7 else "低"
    return {
        "translated_text": f"{state['translated_text']} [品質: {quality}]"
    }


# ============================================================
# 6. 建立父圖
# ============================================================
parent_builder = StateGraph(ParentState)
parent_builder.add_node("preprocess", preprocess)
parent_builder.add_node("translate", call_translation_subgraph)  # <-- 包裝函式
parent_builder.add_node("postprocess", postprocess)

parent_builder.add_edge(START, "preprocess")
parent_builder.add_edge("preprocess", "translate")
parent_builder.add_edge("translate", "postprocess")
parent_builder.add_edge("postprocess", END)

parent_graph = parent_builder.compile()


# ============================================================
# 7. 執行
# ============================================================
result = parent_graph.invoke({
    "original_text": "  LangGraph 是一個強大的 AI 代理框架  ",
    "source_lang": "zh",
    "target_lang": "en",
    "translated_text": "",
    "quality_score": 0.0
})

print(f"原文: {result['original_text']}")
print(f"翻譯: {result['translated_text']}")
print(f"品質分數: {result['quality_score']}")
