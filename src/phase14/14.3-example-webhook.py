# 14.3 範例：Webhook 完整使用
# 展示如何在 run 完成後觸發 webhook 通知
# 需要：pip install langgraph-sdk flask
# 需要：Agent Server 運行中（langgraph dev）

from langgraph_sdk import get_client

# ============================================================
# 範例 1：基本 Webhook 使用
# ============================================================
async def webhook_basic():
    """在 streaming run 完成後觸發 webhook"""
    client = get_client(url="http://localhost:2024")

    # 建立 thread
    thread = await client.threads.create()

    # 執行 run 並指定 webhook URL
    async for chunk in client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id="agent",
        input={
            "messages": [{"role": "user", "content": "Hello!"}]
        },
        stream_mode="events",
        # Run 完成後，Agent Server 會 POST 到這個 URL
        webhook="https://my-server.app/my-webhook-endpoint",
    ):
        pass  # 處理 streaming 事件


# ============================================================
# 範例 2：Webhook 接收端（Flask 範例）
# ============================================================
# pip install flask
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/my-webhook-endpoint", methods=["POST"])
def handle_webhook():
    """
    接收 Agent Server 的 webhook 通知
    Payload 包含 run 完整資訊
    """
    payload = request.json

    # 提取關鍵資訊
    run_id = payload.get("run_id")
    status = payload.get("status")          # "success" 或 "error"
    thread_id = payload.get("thread_id")
    values = payload.get("values", {})       # 最終 state values
    error = payload.get("error")             # 失敗時的錯誤資訊

    print(f"Run {run_id} completed with status: {status}")

    if status == "success":
        # 處理成功的 run
        messages = values.get("messages", [])
        print(f"Agent 回覆: {messages[-1] if messages else 'N/A'}")
    elif error:
        # 處理失敗的 run
        print(f"Error: {error['error']} - {error['message']}")

    return jsonify({"received": True}), 200

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)
