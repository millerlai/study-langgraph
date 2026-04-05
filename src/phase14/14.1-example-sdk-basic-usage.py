# 14.1 範例：LangGraph SDK 基本使用
# 展示如何透過 SDK 與已部署的 Agent Server 互動
# 需要：pip install langgraph-sdk
# 需要：Agent Server 運行中（langgraph dev）

from langgraph_sdk import get_client, get_sync_client


# === 非同步客戶端 ===
async def async_example():
    client = get_client(
        url="http://localhost:2024",
        api_key="your-langsmith-api-key"  # 部署環境需要
    )

    # 建立 thread
    thread = await client.threads.create()
    print(f"Thread ID: {thread['thread_id']}")

    # 執行 graph（streaming）
    async for chunk in client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id="agent",  # langgraph.json 中定義的名稱
        input={
            "messages": [{"role": "human", "content": "你好！"}]
        },
        stream_mode="updates",
    ):
        print(f"Event: {chunk.event}")
        print(f"Data: {chunk.data}\n")


# === 同步客戶端 ===
def sync_example():
    client = get_sync_client(url="http://localhost:2024")

    # Threadless run（無狀態執行）
    for chunk in client.runs.stream(
        None,       # thread_id=None 表示無狀態執行
        "agent",
        input={
            "messages": [{"role": "human", "content": "Hello!"}]
        },
        stream_mode="updates",
    ):
        print(f"Event: {chunk.event}, Data: {chunk.data}")


if __name__ == "__main__":
    sync_example()
