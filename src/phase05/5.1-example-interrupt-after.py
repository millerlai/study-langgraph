# 5.1 範例：interrupt_after - 在節點執行完之後暫停
# 展示使用 interrupt_after 來檢查節點的輸出後再決定是否繼續
"""
interrupt_after：在節點執行完「之後」暫停
適合用來檢查節點的輸出
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

class State(TypedDict):
    query: str
    search_results: list[str]
    summary: str

def search(state: State) -> dict:
    """搜尋"""
    return {"search_results": ["結果A", "結果B", "結果C"]}

def summarize(state: State) -> dict:
    """摘要"""
    return {"summary": f"根據 {len(state['search_results'])} 筆結果生成摘要"}

builder = StateGraph(State)
builder.add_node("search", search)
builder.add_node("summarize", summarize)
builder.add_edge(START, "search")
builder.add_edge("search", "summarize")
builder.add_edge("summarize", END)

checkpointer = MemorySaver()
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_after=["search"],  # search 執行完後暫停
)

config = {"configurable": {"thread_id": "after-bp-1"}}

# 執行到 search 完成後暫停
graph.invoke({"query": "LangGraph", "search_results": [], "summary": ""}, config=config)

state = graph.get_state(config)
print(f"搜尋結果: {state.values['search_results']}")
# 搜尋結果: ['結果A', '結果B', '結果C']
print(f"下一步: {state.next}")
# 下一步: ('summarize',)

# 人類檢查搜尋結果後，決定繼續
result = graph.invoke(Command(resume=True), config=config)
print(f"摘要: {result['summary']}")
# 摘要: 根據 3 筆結果生成摘要
