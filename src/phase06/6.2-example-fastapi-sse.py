# 6.2 範例：FastAPI + LangGraph astream() 整合 SSE
# 展示透過 Server-Sent Events 將串流推送給前端的模式
# 注意：完整的 FastAPI 整合需安裝 fastapi, uvicorn, sse-starlette
"""
FastAPI + LangGraph astream() 整合
透過 Server-Sent Events 將串流推送給前端
（需安裝 fastapi, uvicorn, sse-starlette）
"""
import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer

# -- 圖定義 --
class State(TypedDict):
    query: str
    result: str


def process_query(state: State) -> dict:
    writer = get_stream_writer()
    writer({"status": "processing"})
    return {"result": f"已處理: {state['query']}"}


graph = (
    StateGraph(State)
    .add_node("process", process_query)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)

# -- FastAPI 應用（註解版，需安裝額外套件才能執行） --
# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
#
# app = FastAPI()
#
# async def event_generator(query: str):
#     async for chunk in graph.astream(
#         {"query": query},
#         stream_mode=["updates", "custom"],
#         version="v2",
#     ):
#         yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
#     yield "data: [DONE]\n\n"
#
# @app.get("/stream")
# async def stream_endpoint(query: str = "test"):
#     return StreamingResponse(
#         event_generator(query),
#         media_type="text/event-stream",
#     )

# 獨立測試（不啟動伺服器）
import asyncio

async def test_stream():
    print("=== FastAPI SSE 模擬 ===")
    async for chunk in graph.astream(
        {"query": "Hello LangGraph"},
        stream_mode=["updates", "custom"],
        version="v2",
    ):
        sse_data = json.dumps(chunk, ensure_ascii=False)
        print(f"  data: {sse_data}")
    print("  data: [DONE]")

asyncio.run(test_stream())
