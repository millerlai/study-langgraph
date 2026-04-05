# 16.3 範例：加密 Checkpointer + 時間旅行
# 展示加密序列化在實際應用中的完整流程
# 需要：pip install langgraph
# 真實加密需要：pip install pycryptodome langgraph-checkpoint-sqlite
# 真實加密需要：設定 LANGGRAPH_AES_KEY 環境變數

import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


class SecureState(TypedDict):
    user_input: NotRequired[str]
    api_key: NotRequired[str]       # 敏感資料！
    result: NotRequired[str]


def mask_key(state: SecureState) -> dict:
    """遮蔽 API key"""
    key = state.get("api_key", "")
    masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return {"api_key": masked}


def process(state: SecureState) -> dict:
    return {"result": f"已用 {state['api_key']} 處理: {state['user_input']}"}


# 在真實場景中，使用 EncryptedSerializer：
# from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
# serde = EncryptedSerializer.from_pycryptodome_aes()
# checkpointer = SqliteSaver(conn, serde=serde)

# 此處用 InMemorySaver 示範流程
checkpointer = InMemorySaver(serde=JsonPlusSerializer())

graph = (
    StateGraph(SecureState)
    .add_node("mask", mask_key)
    .add_node("process", process)
    .add_edge(START, "mask")
    .add_edge("mask", "process")
    .add_edge("process", END)
    .compile(checkpointer=checkpointer)
)

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke(
    {"user_input": "查詢餘額", "api_key": "sk-1234567890abcdef"},
    config,
)

print(f"結果: {result}")

# 驗證 checkpoint 中的 state
saved = graph.get_state(config)
print(f"儲存的 state: {saved.values}")
print(f"API key 已遮蔽: {'****' in saved.values.get('api_key', '')}")

# 查看完整歷史
print("\n完整歷史:")
for state in graph.get_state_history(config):
    print(f"  step={state.metadata['step']}, "
          f"next={state.next}, "
          f"api_key={state.values.get('api_key', 'N/A')}")
