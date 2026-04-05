# 14.3 範例：Background Run 完整使用
# 啟動長時間任務後立即返回，之後查詢結果
# 需要：pip install langgraph-sdk
# 需要：Agent Server 運行中（langgraph dev）

from langgraph_sdk import get_client
import asyncio


async def background_run_example():
    client = get_client(url="http://localhost:2024")

    # === 建立 Thread ===
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    # === 啟動 Background Run ===
    # 立即返回，不等待執行完成
    run = await client.runs.create(
        thread_id=thread_id,
        assistant_id="agent",
        input={
            "messages": [
                {
                    "role": "user",
                    "content": "請分析這份 100 頁的報告並整理重點...",
                }
            ]
        },
    )
    run_id = run["run_id"]
    print(f"Background run started: {run_id}")
    print(f"Status: {run['status']}")  # "pending" 或 "running"

    # === 查詢 Run 狀態 ===
    while True:
        run_status = await client.runs.get(thread_id, run_id)
        status = run_status["status"]
        print(f"Current status: {status}")

        if status in ("success", "error"):
            break

        await asyncio.sleep(2)  # 每 2 秒查詢一次

    # === 取得結果 ===
    if run_status["status"] == "success":
        state = await client.threads.get_state(thread_id)
        print(f"最終結果: {state['values']}")
    else:
        print(f"執行失敗: {run_status}")


    # === 結合 Webhook 使用 ===
    # 更好的做法：不需要 polling，用 webhook 接收通知
    run_with_webhook = await client.runs.create(
        thread_id=thread_id,
        assistant_id="agent",
        input={
            "messages": [
                {"role": "user", "content": "另一個長時間任務"}
            ]
        },
        webhook="https://my-server.app/webhook",
    )
    print(f"Run with webhook: {run_with_webhook['run_id']}")
    # 當 run 完成時，webhook endpoint 會收到 POST 通知


if __name__ == "__main__":
    asyncio.run(background_run_example())
