# 2.3 Private State — Private State + Input/Output Schema 組合使用
# 展示完整的三層 State 隔離設計
# 不需要 API key

"""
Private State + Input/Output Schema 組合使用
展示完整的 State 隔離設計
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 外部輸入
class InputState(TypedDict):
    query: str

# 外部輸出
class OutputState(TypedDict):
    result: str

# 內部完整 State
class InternalState(InputState, OutputState):
    intermediate: str     # 內部用，但在主 State 中

# 私有 State（完全不在主 State 中）
class PrivateAnalysis(TypedDict):
    raw_analysis: str     # 只在 analyze → synthesize 之間傳遞

# Nodes
def analyze(state: InputState) -> PrivateAnalysis:
    """讀取公開輸入，寫入私有分析"""
    return {"raw_analysis": f"analysis of: {state['query']}"}

def synthesize(state: PrivateAnalysis) -> InternalState:
    """讀取私有分析，寫入內部 State"""
    return {
        "intermediate": f"synthesized: {state['raw_analysis']}",
        "result": f"結果: {state['raw_analysis']}",
    }

# Graph（三層隔離：Input → Internal+Private → Output）
builder = StateGraph(
    InternalState,
    input_schema=InputState,
    output_schema=OutputState,
)
builder.add_node("analyze", analyze)
builder.add_node("synthesize", synthesize)
builder.add_edge(START, "analyze")
builder.add_edge("analyze", "synthesize")
builder.add_edge("synthesize", END)

graph = builder.compile()

result = graph.invoke({"query": "什麼是 LangGraph？"})
print(result)
# {"result": "結果: analysis of: 什麼是 LangGraph？"}
#
# 外部看不到：
#   - intermediate（在 InternalState 但不在 OutputState）
#   - raw_analysis（Private State）
