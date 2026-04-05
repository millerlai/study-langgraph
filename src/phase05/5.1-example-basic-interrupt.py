# 5.1 範例：interrupt() 基本用法
# 展示在節點中使用 interrupt() 暫停執行，等待人類輸入後用 Command(resume=...) 恢復
"""
interrupt() 基本範例：在節點中暫停，等待人類輸入
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

# ============================================================
# 1. 定義 State
# ============================================================
class State(TypedDict):
    question: str
    human_feedback: str
    answer: str

# ============================================================
# 2. 定義 Nodes
# ============================================================
def ask_human(state: State) -> dict:
    """此節點會暫停執行，等待人類輸入"""
    question = state["question"]

    # interrupt() 暫停圖的執行
    # 傳入的值會作為中斷的 payload，讓外部知道在等什麼
    feedback = interrupt(f"請針對以下問題提供意見：{question}")

    # 當 Command(resume=...) 恢復執行時，
    # interrupt() 的回傳值就是 resume 傳入的值
    return {"human_feedback": feedback}

def generate_answer(state: State) -> dict:
    """根據人類回饋生成答案"""
    return {
        "answer": f"根據您的回饋「{state['human_feedback']}」，答案是：已處理完成。"
    }

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(State)
builder.add_node("ask_human", ask_human)
builder.add_node("generate_answer", generate_answer)

builder.add_edge(START, "ask_human")
builder.add_edge("ask_human", "generate_answer")
builder.add_edge("generate_answer", END)

# 必須配置 checkpointer！
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 4. 執行：第一次呼叫（會在 interrupt() 暫停）
# ============================================================
config = {"configurable": {"thread_id": "thread-1"}}

print("=== 第一次呼叫：圖會暫停 ===")
for chunk in graph.stream(
    {"question": "LangGraph 適合什麼場景？"},
    config=config,
    stream_mode="values",
):
    print(f"State: {chunk}")

# 輸出：
# === 第一次呼叫：圖會暫停 ===
# State: {'question': 'LangGraph 適合什麼場景？'}
# （圖在 ask_human 節點暫停，不會到 generate_answer）

# ============================================================
# 5. 檢查中斷狀態
# ============================================================
state = graph.get_state(config)
print(f"\n目前停在的節點: {state.next}")
print(f"中斷 payload: {state.tasks}")
# 目前停在的節點: ('ask_human',)
# 中斷 payload 包含 "請針對以下問題提供意見：LangGraph 適合什麼場景？"

# ============================================================
# 6. 恢復執行：用 Command(resume=...) 傳入人類輸入
# ============================================================
print("\n=== 恢復執行 ===")
for chunk in graph.stream(
    Command(resume="適合需要複雜控制流的 AI 應用"),
    config=config,
    stream_mode="values",
):
    print(f"State: {chunk}")

# 輸出：
# === 恢復執行 ===
# State: {'question': 'LangGraph 適合什麼場景？', 'human_feedback': '適合需要複雜控制流的 AI 應用'}
# State: {'question': 'LangGraph 適合什麼場景？', 'human_feedback': '適合需要複雜控制流的 AI 應用', 'answer': '根據您的回饋「適合需要複雜控制流的 AI 應用」，答案是：已處理完成。'}
