# 12.3 範例：在 LangGraph 中直接使用非 LangChain API
# 示範在 Task 中直接呼叫任何 API，不需要 LangChain 的 ChatModel wrapper
# 此範例使用模擬回應，不需要 API key

import uuid
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

# ============================================================
# 方法一：直接使用 OpenAI SDK
# ============================================================
@task
def call_openai_direct(prompt: str) -> str:
    """直接使用 openai SDK（不透過 LangChain）"""
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return response.choices[0].message.content
    return f"[OpenAI 直接呼叫] 回應: {prompt}"  # 模擬

# ============================================================
# 方法二：直接使用 requests 呼叫任意 API
# ============================================================
@task
def call_custom_llm(prompt: str) -> str:
    """呼叫自建的 LLM API"""
    # import requests
    # response = requests.post(
    #     "http://my-llm-server:8080/v1/chat",
    #     json={
    #         "messages": [{"role": "user", "content": prompt}],
    #         "max_tokens": 500,
    #         "temperature": 0.7,
    #     },
    #     headers={"Authorization": "Bearer MY_TOKEN"},
    #     timeout=30,
    # )
    # return response.json()["choices"][0]["message"]["content"]
    return f"[自定義 LLM] 回應: {prompt}"  # 模擬

# ============================================================
# 方法三：使用 Ollama 本地模型
# ============================================================
@task
def call_ollama(prompt: str) -> str:
    """呼叫本地 Ollama 模型"""
    # import requests
    # response = requests.post(
    #     "http://localhost:11434/api/chat",
    #     json={
    #         "model": "llama3",
    #         "messages": [{"role": "user", "content": prompt}],
    #         "stream": False,
    #     },
    # )
    # return response.json()["message"]["content"]
    return f"[Ollama 本地] 回應: {prompt}"  # 模擬

# ============================================================
# 在 Functional API 中組合使用
# ============================================================
checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def multi_llm_workflow(inputs: dict) -> dict:
    """同時呼叫多個 LLM 並比較結果"""
    prompt = inputs["prompt"]

    # 並行呼叫三個不同的 LLM
    future_openai = call_openai_direct(prompt)
    future_custom = call_custom_llm(prompt)
    future_ollama = call_ollama(prompt)

    return {
        "openai": future_openai.result(),
        "custom": future_custom.result(),
        "ollama": future_ollama.result(),
    }

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = multi_llm_workflow.invoke({"prompt": "解釋量子計算"}, config=config)

for provider, response in result.items():
    print(f"{provider}: {response}")
# 輸出:
# openai: [OpenAI 直接呼叫] 回應: 解釋量子計算
# custom: [自定義 LLM] 回應: 解釋量子計算
# ollama: [Ollama 本地] 回應: 解釋量子計算
