# 5.2 範例：工具呼叫審核模式
# 展示 Agent 選擇工具後暫停等待人類批准（approve/reject/modify）的完整流程
"""
工具呼叫審核模式：Agent 選擇工具後暫停，等待人類批准
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
import operator

# ============================================================
# 1. 定義工具與 State
# ============================================================
AVAILABLE_TOOLS = {
    "search": lambda q: f"搜尋結果：找到關於「{q}」的 3 篇文章",
    "send_email": lambda to: f"已發送 email 給 {to}",
    "delete_file": lambda path: f"已刪除檔案 {path}",
}

# 高風險工具需要人類批准
HIGH_RISK_TOOLS = {"send_email", "delete_file"}

class State(TypedDict):
    user_request: str
    tool_name: str
    tool_args: dict
    tool_result: str
    logs: Annotated[list[str], operator.add]

# ============================================================
# 2. 定義 Nodes
# ============================================================
def plan_tool_call(state: State) -> dict:
    """Agent 規劃要使用哪個工具（模擬 LLM 規劃）"""
    request = state["user_request"]

    # 模擬 Agent 決定使用的工具
    if "搜尋" in request or "查" in request:
        return {
            "tool_name": "search",
            "tool_args": {"q": request},
            "logs": ["Agent 規劃使用 search 工具"],
        }
    elif "email" in request or "寄" in request:
        return {
            "tool_name": "send_email",
            "tool_args": {"to": "user@example.com"},
            "logs": ["Agent 規劃使用 send_email 工具"],
        }
    else:
        return {
            "tool_name": "delete_file",
            "tool_args": {"path": "/tmp/data.csv"},
            "logs": ["Agent 規劃使用 delete_file 工具"],
        }

def review_tool_call(state: State) -> dict:
    """審核工具呼叫——高風險工具需要人類批准"""
    tool_name = state["tool_name"]
    tool_args = state["tool_args"]

    if tool_name in HIGH_RISK_TOOLS:
        # 中斷，等待人類審核
        decision = interrupt({
            "message": "以下工具呼叫需要您的批准",
            "tool": tool_name,
            "args": tool_args,
            "options": ["approve", "reject", "modify"],
        })

        if decision == "reject":
            return {
                "tool_result": f"工具 {tool_name} 被人類拒絕執行",
                "logs": [f"人類拒絕了 {tool_name} 的執行"],
            }
        elif isinstance(decision, dict) and decision.get("action") == "modify":
            # 人類修改了工具參數
            return {
                "tool_args": decision.get("new_args", tool_args),
                "logs": [f"人類修改了 {tool_name} 的參數"],
            }
        else:
            return {"logs": [f"人類批准了 {tool_name} 的執行"]}
    else:
        return {"logs": [f"{tool_name} 是低風險工具，自動批准"]}

def execute_tool(state: State) -> dict:
    """實際執行工具"""
    tool_name = state["tool_name"]
    tool_args = state["tool_args"]

    if "被人類拒絕" in state.get("tool_result", ""):
        return {"logs": ["跳過執行（已被拒絕）"]}

    tool_fn = AVAILABLE_TOOLS[tool_name]
    first_arg = list(tool_args.values())[0]
    result = tool_fn(first_arg)

    return {
        "tool_result": result,
        "logs": [f"工具執行結果: {result}"],
    }

def should_execute(state: State) -> str:
    """條件邊：判斷是否執行工具"""
    if "被人類拒絕" in state.get("tool_result", ""):
        return "end"
    return "execute"

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(State)
builder.add_node("plan_tool_call", plan_tool_call)
builder.add_node("review_tool_call", review_tool_call)
builder.add_node("execute_tool", execute_tool)

builder.add_edge(START, "plan_tool_call")
builder.add_edge("plan_tool_call", "review_tool_call")
builder.add_conditional_edges(
    "review_tool_call",
    should_execute,
    {"execute": "execute_tool", "end": END},
)
builder.add_edge("execute_tool", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ============================================================
# 4. 測試：低風險工具（自動執行，不暫停）
# ============================================================
print("=== 低風險工具：search ===")
config_low = {"configurable": {"thread_id": "low-risk-tool"}}
result = graph.invoke(
    {"user_request": "搜尋 LangGraph 教學", "tool_name": "", "tool_args": {},
     "tool_result": "", "logs": []},
    config=config_low,
)
print(f"結果: {result['tool_result']}")
print(f"日誌: {result['logs']}")
# 結果: 搜尋結果：找到關於「搜尋 LangGraph 教學」的 3 篇文章
# 日誌: ['Agent 規劃使用 search 工具', 'search 是低風險工具，自動批准', '工具執行結果: ...']

# ============================================================
# 5. 測試：高風險工具（暫停等待批准）
# ============================================================
print("\n=== 高風險工具：delete_file ===")
config_high = {"configurable": {"thread_id": "high-risk-tool"}}
graph.invoke(
    {"user_request": "清理暫存檔案", "tool_name": "", "tool_args": {},
     "tool_result": "", "logs": []},
    config=config_high,
)

state = graph.get_state(config_high)
print(f"暫停在: {state.next}")
# 暫停在: ('review_tool_call',)

# 人類批准
result = graph.invoke(Command(resume="approve"), config=config_high)
print(f"批准後結果: {result['tool_result']}")
print(f"日誌: {result['logs']}")
# 批准後結果: 已刪除檔案 /tmp/data.csv
# 日誌: [..., '人類批准了 delete_file 的執行', '工具執行結果: 已刪除檔案 /tmp/data.csv']

# ============================================================
# 6. 測試：高風險工具（人類拒絕）
# ============================================================
print("\n=== 高風險工具：拒絕 ===")
config_reject = {"configurable": {"thread_id": "reject-tool"}}
graph.invoke(
    {"user_request": "寄 email 給客戶", "tool_name": "", "tool_args": {},
     "tool_result": "", "logs": []},
    config=config_reject,
)

result = graph.invoke(Command(resume="reject"), config=config_reject)
print(f"拒絕後結果: {result['tool_result']}")
# 拒絕後結果: 工具 send_email 被人類拒絕執行
