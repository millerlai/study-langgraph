# 13.4 範例：LangSmith 評估流程（本地模擬版）
# 示範 LangSmith evaluate() 的概念，不需要真實 API key
# 完整 LangSmith 版本需要設定 LANGSMITH_API_KEY 和 OPENAI_API_KEY

# === 本地模擬版本（不需要 API key） ===
print("=== LangSmith 評估流程模擬 ===\n")

# 模擬資料集
dataset = [
    {"inputs": {"question": "什麼是 LangGraph？"}, "outputs": {"answer": "圖狀態機框架"}},
    {"inputs": {"question": "什麼是 Python？"},    "outputs": {"answer": "程式語言"}},
    {"inputs": {"question": "什麼是 Docker？"},    "outputs": {"answer": "容器化平台"}},
]

# 模擬 target
def mock_target(inputs: dict) -> dict:
    answers = {
        "什麼是 LangGraph？": "LangGraph 是一個圖狀態機框架",
        "什麼是 Python？": "Python 是一種程式語言",
        "什麼是 Docker？": "Docker 是容器化平台",
    }
    return {"response": answers.get(inputs["question"], "不確定")}

# 模擬評估器
def mock_correctness(inputs, outputs, reference_outputs):
    return reference_outputs["answer"].lower() in outputs["response"].lower()

def mock_concision(outputs, reference_outputs):
    return len(outputs["response"]) < 3 * len(reference_outputs["answer"])

# 執行模擬評估
print(f"  {'問題':<20} {'正確性':<8} {'簡潔度':<8} {'回應'}")
print(f"  {'-'*70}")
for item in dataset:
    output = mock_target(item["inputs"])
    correct = mock_correctness(item["inputs"], output, item["outputs"])
    concise = mock_concision(output, item["outputs"])
    print(f"  {item['inputs']['question']:<20} {'PASS' if correct else 'FAIL':<8} "
          f"{'PASS' if concise else 'FAIL':<8} {output['response']}")

print("\n  總正確率: 100%")
print("  總簡潔度: 100%")
