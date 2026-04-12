# 1.3 第一個 Graph — 範例一：基本聊天機器人
# 使用 StateGraph + MessagesState，最簡單的 START → llm → END 線性流程
# 需要設定 OPENAI_API_KEY 環境變數

"""
範例一：基本聊天機器人
- 使用 StateGraph + MessagesState
- 單一 LLM 節點
- 最簡單的 START → llm → END 線性流程
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import AnthropicLLM
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, MessagesState, START, END
from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ
# ============================================================
# 1. 初始化 LLM
# ============================================================
#model = ChatOpenAI(model="gpt-5-nano", temperature=0) # Set OPENAI_API_KEY in environment variables, you could create API key at https://platform.openai.com/settings/organization/api-keys

model = ChatAnthropic(model="claude-sonnet-4-5") # Set ANTHROPIC_API_KEY in environment variables , you could create API key at https://platform.claude.com/settings/keys

# ============================================================
# 2. 定義 Node
# ============================================================
def chatbot(state: MessagesState) -> dict:
    """
    聊天機器人節點：
    - 讀取 state["messages"]（完整對話歷史）
    - 呼叫 LLM
    - 回傳新的 AI 訊息
    """
    response = model.invoke(state["messages"])
    # 回傳 dict，LangGraph 會用 add_messages reducer
    # 將新訊息追加到 messages 列表
    return {"messages": [response]}

# ============================================================
# 3. 建構 Graph
# ============================================================
builder = StateGraph(MessagesState)

# 註冊節點
builder.add_node("chatbot", chatbot)

# 定義邊：START → chatbot → END
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# 編譯成可執行的 Graph
graph = builder.compile()

# ============================================================
# 4. 執行
# ============================================================
result = graph.invoke({
    "messages": [{"role": "user", "content": "你好！請用一句話介紹 LangGraph。"}]
})

# 印出 AI 的回應
print(result["messages"][-1].content)
