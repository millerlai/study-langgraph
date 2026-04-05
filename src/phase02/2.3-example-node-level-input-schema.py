# 2.3 Private State — Node-Level Input Schema
# 展示如何用參數型別控制節點可見的 State 範圍（最小權限原則）
# 不需要 API key

"""
Node-Level Input Schema
展示如何用參數型別控制節點可見的 State 範圍
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# ============================================================
# 1. 主 State
# ============================================================
class MainState(TypedDict):
    user_input: str
    processed: str
    final_output: str

# ============================================================
# 2. 限制節點可見範圍的 Schema
# ============================================================
class ProcessorInput(TypedDict):
    user_input: str        # 只看得到 user_input

class ProcessorOutput(TypedDict):
    processed: str         # 只寫入 processed

class FormatterInput(TypedDict):
    processed: str         # 只看得到 processed

# ============================================================
# 3. 節點——每個節點只看到自己需要的部分
# ============================================================
def processor(state: ProcessorInput) -> ProcessorOutput:
    """只看得到 user_input，只寫入 processed"""
    # state 中只有 user_input，看不到 final_output
    return {"processed": f"已處理: {state['user_input']}"}

def formatter(state: FormatterInput) -> MainState:
    """只看得到 processed，寫入 final_output"""
    # state 中只有 processed，看不到 user_input
    return {"final_output": f"最終: {state['processed']}"}

# ============================================================
# 4. 建構與執行
# ============================================================
builder = StateGraph(MainState)
builder.add_node("processor", processor)
builder.add_node("formatter", formatter)
builder.add_edge(START, "processor")
builder.add_edge("processor", "formatter")
builder.add_edge("formatter", END)

graph = builder.compile()

result = graph.invoke({
    "user_input": "Hello",
    "processed": "",
    "final_output": "",
})

print(result)
# {
#     "user_input": "Hello",
#     "processed": "已處理: Hello",
#     "final_output": "最終: 已處理: Hello"
# }
