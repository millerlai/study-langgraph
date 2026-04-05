# 12.1 範例：手動用 Graph API 實作 ReAct 迴圈
# 示範完全控制每一步行為的 ReAct Agent（使用模擬 LLM）

from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.tools import tool

# ============================================================
# 1. 定義工具
# ============================================================
@tool
def add(a: int, b: int) -> int:
    """兩個數字相加。"""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """兩個數字相乘。"""
    return a * b

tools = [add, multiply]

# ============================================================
# 2. 定義 State
# ============================================================
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# ============================================================
# 3. 定義模擬 LLM 節點（真實應用換成 ChatModel）
# ============================================================
call_index = 0

def agent_node(state: AgentState) -> dict:
    """模擬 LLM 的推理過程"""
    global call_index
    call_index += 1

    messages = state["messages"]
    last_msg = messages[-1]

    # 第一次呼叫：決定使用 multiply 工具
    if call_index == 1:
        return {
            "messages": [AIMessage(
                content="我需要先計算 3 x 5",
                tool_calls=[{
                    "id": "call_1",
                    "name": "multiply",
                    "args": {"a": 3, "b": 5}
                }]
            )]
        }
    # 第二次呼叫：拿到乘法結果後，使用 add
    elif call_index == 2:
        prev_result = messages[-1].content  # ToolMessage 的內容
        return {
            "messages": [AIMessage(
                content=f"乘法結果是 {prev_result}，現在加上 10",
                tool_calls=[{
                    "id": "call_2",
                    "name": "add",
                    "args": {"a": int(prev_result), "b": 10}
                }]
            )]
        }
    # 第三次呼叫：有足夠資訊，給出最終答案
    else:
        prev_result = messages[-1].content
        return {
            "messages": [AIMessage(
                content=f"計算完成！3 x 5 + 10 = {prev_result}"
            )]
        }

# ============================================================
# 4. 建立圖
# ============================================================
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# ============================================================
# 5. 執行
# ============================================================
result = graph.invoke({
    "messages": [HumanMessage(content="請計算 3 x 5 + 10")]
})

print("=== ReAct 迴圈執行過程 ===")
for msg in result["messages"]:
    name = msg.__class__.__name__
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        calls = ", ".join(f"{tc['name']}({tc['args']})" for tc in msg.tool_calls)
        print(f"  {name}: {msg.content} → 呼叫工具: {calls}")
    else:
        print(f"  {name}: {msg.content}")

# 輸出:
#   HumanMessage: 請計算 3 x 5 + 10
#   AIMessage: 我需要先計算 3 x 5 → 呼叫工具: multiply({'a': 3, 'b': 5})
#   ToolMessage: 15
#   AIMessage: 乘法結果是 15，現在加上 10 → 呼叫工具: add({'a': 15, 'b': 10})
#   ToolMessage: 25
#   AIMessage: 計算完成！3 x 5 + 10 = 25
