# 12.3 範例：實作自定義 ChatModel — 完整融入 LangChain 生態系
# 示範繼承 BaseChatModel 實作自家 API 的 wrapper
# 此範例使用模擬回應，不需要 API key

from typing import Any, Iterator, Optional, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, AIMessageChunk
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.callbacks import CallbackManagerForLLMRun

class CustomChatModel(BaseChatModel):
    """自定義 Chat Model，對接自家 API"""

    api_url: str = "http://localhost:8080/v1/chat"
    api_key: str = ""
    model_name: str = "custom-model-v1"
    temperature: float = 0.7

    @property
    def _llm_type(self) -> str:
        return "custom-chat-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """核心生成方法：呼叫你的 API"""

        # 轉換 messages 為你的 API 格式
        api_messages = []
        for msg in messages:
            role = "user" if msg.type == "human" else "assistant"
            api_messages.append({"role": role, "content": msg.content})

        # 模擬 API 呼叫（實際應用換成 requests.post）
        content = f"[{self.model_name}] 收到 {len(messages)} 則訊息，溫度={self.temperature}"

        return ChatResult(
            generations=[
                ChatGeneration(message=AIMessage(content=content))
            ]
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """串流生成方法"""
        # 模擬串流回應
        content = f"[{self.model_name}] 串流回應"
        for char in content:
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=char)
            )

# ============================================================
# 使用自定義 ChatModel
# ============================================================
model = CustomChatModel(
    api_url="http://my-api.example.com/v1/chat",
    api_key="sk-xxx",
    model_name="my-llm-v2",
    temperature=0.3,
)

# 跟標準 LangChain ChatModel 一樣使用
response = model.invoke([{"role": "user", "content": "你好"}])
print(f"回應: {response.content}")

# 串流
for chunk in model.stream([{"role": "user", "content": "你好"}]):
    print(chunk.content, end="")
print()

# 在 LangGraph 中使用
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def agent_node(state: State):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
graph = builder.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "你好"}]})
print(f"圖輸出: {result['messages'][-1].content}")
# 輸出:
# 回應: [my-llm-v2] 收到 1 則訊息，溫度=0.3
# [my-llm-v2] 串流回應
# 圖輸出: [my-llm-v2] 收到 1 則訊息，溫度=0.3
