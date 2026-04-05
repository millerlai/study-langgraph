# 14.3 範例：Cron Job 完整使用
# 展示有狀態和無狀態兩種 cron job
# 需要：pip install langgraph-sdk
# 需要：Agent Server 運行中（langgraph dev）

from langgraph_sdk import get_client


async def cron_examples():
    client = get_client(url="http://localhost:2024")
    assistant_id = "agent"

    # ========================================================
    # 範例 1：有狀態 Cron（綁定特定 Thread）
    # ========================================================
    # 每次執行都在同一個 thread 上，保持對話歷史
    thread = await client.threads.create()
    print(f"Thread: {thread['thread_id']}")

    # 建立 cron job — 每天 UTC 15:27 執行
    cron_job = await client.crons.create_for_thread(
        thread["thread_id"],
        assistant_id,
        schedule="27 15 * * *",       # Cron 表達式（UTC）
        input={
            "messages": [
                {"role": "user", "content": "請給我今天的新聞摘要"}
            ]
        },
    )
    print(f"Cron Job ID: {cron_job['cron_id']}")

    # ========================================================
    # 範例 2：無狀態 Cron（每次建立新 Thread）
    # ========================================================
    # 適合不需要保持歷史的場景
    cron_job_stateless = await client.crons.create(
        assistant_id,
        schedule="0 8 * * 1",          # 每週一 UTC 08:00
        input={
            "messages": [
                {"role": "user", "content": "整理本週的待辦事項並發送郵件"}
            ]
        },
    )
    print(f"Stateless Cron ID: {cron_job_stateless['cron_id']}")

    # ========================================================
    # 範例 3：保留 Thread 的無狀態 Cron
    # ========================================================
    # 預設 "delete" 會在 run 完成後刪除 thread
    # 使用 "keep" 可保留 thread 供後續查詢
    cron_keep = await client.crons.create(
        assistant_id,
        schedule="27 15 * * *",
        input={
            "messages": [
                {"role": "user", "content": "Daily report"}
            ]
        },
        on_run_completed="keep",  # 保留 thread
    )

    # 查詢該 cron 的歷史 runs
    runs = await client.runs.search(
        metadata={"cron_id": cron_keep["cron_id"]}
    )
    print(f"歷史 runs 數量: {len(runs)}")

    # ========================================================
    # 清理：刪除不再需要的 Cron Job（非常重要！）
    # ========================================================
    await client.crons.delete(cron_job["cron_id"])
    await client.crons.delete(cron_job_stateless["cron_id"])
    await client.crons.delete(cron_keep["cron_id"])
    print("所有 Cron Jobs 已刪除")
