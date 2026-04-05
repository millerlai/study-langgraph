# 15.1 範例：LangSmith 離線評估
# 評估 LangGraph agent 的回答品質
# 需要：pip install langsmith
# 需要：設定 LANGSMITH_API_KEY 環境變數

import os
from langsmith import Client
from langsmith.evaluation import evaluate

os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_xxxxx"

# === 初始化 LangSmith Client ===
ls_client = Client()


# === 步驟 1：建立 Dataset ===
dataset_name = "agent-qa-test-v1"

# 建立 dataset（如果不存在）
dataset = ls_client.create_dataset(
    dataset_name,
    description="Agent 問答品質測試集",
)

# 新增測試案例
ls_client.create_examples(
    inputs=[
        {"question": "LangGraph 是什麼？"},
        {"question": "如何在 LangGraph 中使用 Human-in-the-Loop？"},
        {"question": "LangGraph 與 LangChain 有什麼不同？"},
    ],
    outputs=[
        {"answer": "LangGraph 是一個低階的有狀態 AI Agent 編排框架"},
        {"answer": "使用 interrupt() 函數暫停執行，等待人類輸入"},
        {"answer": "LangGraph 專注於 agent 編排，LangChain 專注於 LLM 應用鏈"},
    ],
    dataset_id=dataset.id,
)


# === 步驟 2：定義目標函數（被評估的 agent） ===
def agent_target(inputs: dict) -> dict:
    """
    這是被評估的 agent 函數
    在實際場景中，這會是你的 LangGraph agent
    """
    # 假設我們有一個已編譯的 graph
    # result = app.invoke({"messages": [{"role": "user", "content": inputs["question"]}]})
    # return {"answer": result["messages"][-1].content}

    # 模擬回答
    return {"answer": f"這是關於 '{inputs['question']}' 的回答。"}


# === 步驟 3：定義 Evaluators ===
def correctness_evaluator(run, example) -> dict:
    """
    Code-based evaluator：檢查回答是否包含關鍵字
    """
    prediction = run.outputs.get("answer", "")
    reference = example.outputs.get("answer", "")

    # 簡單的關鍵字匹配
    keywords = reference.lower().split()
    matches = sum(1 for kw in keywords if kw in prediction.lower())
    score = matches / len(keywords) if keywords else 0

    return {
        "key": "correctness",
        "score": score,
        "comment": f"匹配 {matches}/{len(keywords)} 個關鍵字",
    }


def length_evaluator(run, example) -> dict:
    """
    Code-based evaluator：檢查回答長度是否合理
    """
    answer = run.outputs.get("answer", "")
    length = len(answer)

    if length < 10:
        score = 0.0
        comment = "回答太短"
    elif length > 2000:
        score = 0.5
        comment = "回答太長"
    else:
        score = 1.0
        comment = "長度適中"

    return {"key": "length", "score": score, "comment": comment}


# === 步驟 4：執行評估 ===
results = evaluate(
    agent_target,
    data=dataset_name,
    evaluators=[correctness_evaluator, length_evaluator],
    experiment_prefix="agent-v1",
    max_concurrency=2,
)

# 結果會自動上傳到 LangSmith Dashboard
print(f"評估完成！共 {len(results)} 個測試案例")
for r in results:
    print(f"  - {r}")
