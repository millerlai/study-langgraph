# 14.3 範例：在 Graph Node 中存取認證使用者資訊
# 搭配 14.3-example-auth.py 使用
# 需要：pip install langgraph langchain-core

from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def my_node(state: State, config: RunnableConfig) -> dict:
    """
    Node 可以從 config 中取得認證使用者資訊
    """
    # 取得使用者資訊
    user_config = config["configurable"].get("langgraph_auth_user", {})
    github_token = user_config.get("github_token", "")
    identity = user_config.get("identity", "anonymous")

    # 使用使用者的 token 進行操作
    return {
        "messages": [
            {
                "role": "assistant",
                "content": f"已驗證用戶 {identity}，可以存取 GitHub。",
            }
        ]
    }


# 建構 Graph
builder = StateGraph(State)
builder.add_node("node", my_node)
builder.add_edge(START, "node")
builder.add_edge("node", END)
graph = builder.compile()
