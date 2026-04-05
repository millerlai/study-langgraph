# 13.4 範例：基本多輪 Chatbot 模擬測試
# 不依賴外部模擬套件，純用 LangGraph 邏輯示範
# 此範例不需要 API key，可直接執行

from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END


class Message(TypedDict):
    role: str
    content: str


class SimState(TypedDict):
    messages: Annotated[list[Message], add]
    turn: int
    max_turns: int


# === 模擬使用者 ===
SIMULATED_USER_QUERIES = [
    "我買的手機螢幕壞了，要退貨！",
    "我上週才買的，為什麼不能退？",
    "好吧，那你們可以修理嗎？",
    "修理要多久？",
    "可以接受，謝謝。",
]


def simulated_user(state: SimState) -> dict:
    turn = state["turn"]
    if turn < len(SIMULATED_USER_QUERIES):
        msg = {"role": "user", "content": SIMULATED_USER_QUERIES[turn]}
    else:
        msg = {"role": "user", "content": "好的，再見。"}
    return {"messages": [msg], "turn": turn + 1}


# === 你的 Chatbot ===
def chatbot(state: SimState) -> dict:
    last_msg = state["messages"][-1]["content"]

    # 簡單的規則式回應（實際場景中會呼叫 LLM）
    if "退貨" in last_msg or "退" in last_msg:
        reply = "很抱歉聽到您的問題。根據我們的政策，購買 7 天內可以退貨，請問您是什麼時候購買的？"
    elif "修理" in last_msg:
        reply = "可以的，我們提供免費保固維修服務。請您把手機寄到我��的服務中心。"
    elif "多久" in last_msg:
        reply = "一般維修需要 3-5 個工作天，我們會盡快處理。"
    elif "謝謝" in last_msg or "再見" in last_msg:
        reply = "不客氣！如有其他問題歡迎隨時聯繫我們。祝您有美好���一天！"
    else:
        reply = "我了解您的情況，讓我為您查看可能的解決方��。"

    return {"messages": [{"role": "assistant", "content": reply}]}


# === 路由：決定繼續或結束 ===
def should_continue(state: SimState) -> str:
    if state["turn"] >= state["max_turns"]:
        return "end"
    # 檢查最後一則訊息是否是結束語
    last_msg = state["messages"][-1]["content"]
    if "再���" in last_msg or "謝謝" in last_msg:
        return "end"
    return "continue"


# === 建構模擬圖 ===
graph = (
    StateGraph(SimState)
    .add_node("user", simulated_user)
    .add_node("chatbot", chatbot)
    .add_edge(START, "user")
    .add_edge("user", "chatbot")
    .add_conditional_edges(
        "chatbot",
        should_continue,
        {"continue": "user", "end": END},
    )
    .compile()
)

# === 執行模擬 ===
print("=== Chatbot 模擬測試 ===\n")
result = graph.invoke({
    "messages": [],
    "turn": 0,
    "max_turns": 5,
})

for msg in result["messages"]:
    role_label = "使用者" if msg["role"] == "user" else "客服  "
    print(f"  [{role_label}] {msg['content']}")

print(f"\n總共 {len(result['messages'])} 則訊息，{result['turn']} 輪對話")
