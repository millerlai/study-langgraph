# 13.4 範��：基準測試 — 比較不同版本的 Chatbot 表現
# 不需要 LangSmith，純本地執行
# 此範例不需要 API key，可直接執行

from typing import TypedDict


# === 測試資料集 ===
dataset = [
    {"input": "什麼是 LangGraph？", "expected": "圖狀態機框架"},
    {"input": "什麼是 Python？",    "expected": "程式語言"},
    {"input": "什麼是 AI？",        "expected": "人工智慧"},
    {"input": "什麼是 REST API？",  "expected": "網路介面標準"},
    {"input": "什麼是 Docker？",    "expected": "容器化平台"},
]


# === 不同版本的 App ===
def app_v1(question: str) -> str:
    """簡短版"""
    answers = {
        "什麼是 LangGraph？": "一個框架",
        "什麼是 Python？": "程式語言",
        "什麼是 AI？": "人工智慧",
        "什麼是 REST API？": "API 標準",
        "什麼是 Docker？": "容器工具",
    }
    return answers.get(question, "不知道")


def app_v2(question: str) -> str:
    """詳細版"""
    answers = {
        "什麼是 LangGraph？": "LangGraph 是一個用於建構 AI 代理的圖狀態機框架，基於 LangChain 建構",
        "什麼是 Python？": "Python 是一種高階通用程式語言，以其簡潔的語法著稱",
        "什麼是 AI？": "AI 即人工智慧，是讓機器模擬人類智慧的技術",
        "什麼是 REST API？": "REST API 是一種遵循 REST 架構的網路介面標準",
        "什麼是 Docker？": "Docker 是一個開源的容器化平台，用於打包和部署應用程式",
    }
    return answers.get(question, "我不確定這個問題的答案")


# === 評估器 ===
def eval_correctness(response: str, expected: str) -> bool:
    """檢查回應是否包含預期的關鍵字"""
    return expected.lower() in response.lower() or response.lower() in expected.lower()


def eval_concision(response: str) -> float:
    """回應越短分數越高（最高 1.0��"""
    length = len(response)
    if length <= 10:
        return 1.0
    elif length <= 30:
        return 0.8
    elif length <= 60:
        return 0.5
    else:
        return 0.3


# === 執行基準測試 ===
def benchmark(app_fn, app_name: str):
    correct = 0
    concision_scores = []

    for item in dataset:
        response = app_fn(item["input"])
        is_correct = eval_correctness(response, item["expected"])
        concision = eval_concision(response)

        correct += int(is_correct)
        concision_scores.append(concision)

    accuracy = correct / len(dataset)
    avg_concision = sum(concision_scores) / len(concision_scores)
    return {
        "app": app_name,
        "accuracy": f"{accuracy:.0%}",
        "concision": f"{avg_concision:.2f}",
    }


# === 比較結果 ===
print("=== 基準測試結果 ===\n")
results = [
    benchmark(app_v1, "v1 (簡短)"),
    benchmark(app_v2, "v2 (詳細)"),
]

print(f"  {'版本':<15} {'正確率':<10} {'簡潔度':<10}")
print(f"  {'-'*35}")
for r in results:
    print(f"  {r['app']:<15} {r['accuracy']:<10} {r['concision']:<10}")
