# 14.2 範例：連接 LangSmith Cloud 部署的 Agent
# 需要：pip install langgraph-sdk
# 需要：LangSmith API Key 和已部署的 Agent

from langgraph_sdk import get_sync_client

# === 建立連接 ===
client = get_sync_client(
    url="https://your-deployment-url.langsmith.com",
    api_key="your-langsmith-api-key"
)

# === 執行 Agent（Threadless run = 無狀態） ===
for chunk in client.runs.stream(
    None,        # Threadless run
    "agent",     # langgraph.json 中定義的 graph 名稱
    input={
        "messages": [
            {"role": "human", "content": "What is LangGraph?"}
        ]
    },
    stream_mode="updates",
):
    print(f"Event: {chunk.event}")
    print(f"Data: {chunk.data}\n")


# === 有狀態執行（使用 Thread） ===
thread = client.threads.create()

result = client.runs.wait(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input={
        "messages": [
            {"role": "human", "content": "記住我叫小明"}
        ]
    },
)
print(f"結果: {result}")

# 同一 thread 繼續對話
result2 = client.runs.wait(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input={
        "messages": [
            {"role": "human", "content": "我剛才說我叫什麼？"}
        ]
    },
)
print(f"結果: {result2}")
