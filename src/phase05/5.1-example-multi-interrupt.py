# 5.1 範例：同一節點多次 interrupt()
# 展示在一個節點中呼叫多次 interrupt()，每次恢復只執行到下一個 interrupt()
"""
一個節點中可以呼叫多次 interrupt()
每次恢復只會執行到下一個 interrupt()
"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

class State(TypedDict):
    name: str
    age: str
    email: str

def collect_info(state: State) -> dict:
    """逐步收集使用者資訊——每個欄位都用 interrupt() 請求"""
    name = interrupt("請輸入您的姓名：")
    age = interrupt("請輸入您的年齡：")
    email = interrupt("請輸入您的 Email：")
    return {"name": name, "age": age, "email": email}

builder = StateGraph(State)
builder.add_node("collect_info", collect_info)
builder.add_edge(START, "collect_info")
builder.add_edge("collect_info", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "multi-interrupt-1"}}

# 第一次：暫停在第一個 interrupt
graph.invoke({"name": "", "age": "", "email": ""}, config=config)
print(f"等待: {graph.get_state(config).next}")  # ('collect_info',)

# 恢復第一個 interrupt — 然後暫停在第二個
graph.invoke(Command(resume="小明"), config=config)
print(f"等待: {graph.get_state(config).next}")  # ('collect_info',)

# 恢復第二個 interrupt — 然後暫停在第三個
graph.invoke(Command(resume="25"), config=config)
print(f"等待: {graph.get_state(config).next}")  # ('collect_info',)

# 恢復第三個 interrupt — 執行完成
result = graph.invoke(Command(resume="ming@example.com"), config=config)
print(f"收集結果: name={result['name']}, age={result['age']}, email={result['email']}")
# 收集結果: name=小明, age=25, email=ming@example.com
