# 16.1 範例：Durable Execution 完整示範
# 模擬一個多步驟資料處理流程，展示故障恢復和 task 使用
# 需要：pip install langgraph

import uuid
import time
from typing import NotRequired
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import task
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy


# === State 定義 ===
class PipelineState(TypedDict):
    source_url: str
    raw_data: NotRequired[str]
    cleaned_data: NotRequired[str]
    analysis: NotRequired[str]
    report: NotRequired[str]


# === Task 定義（封裝副作用） ===
@task
def download_data(url: str) -> str:
    """模擬下載資料（副作用操作）"""
    print(f"    Downloading from {url}...")
    time.sleep(0.5)  # 模擬網路延遲
    return f"Raw data from {url}"


@task
def call_llm_for_analysis(data: str) -> str:
    """模擬 LLM 分析（可能超時的操作）"""
    print(f"    Analyzing data ({len(data)} chars)...")
    time.sleep(0.3)
    return f"Analysis: {data} has been analyzed. Key findings: ..."


# === Node 定義 ===
def fetch_data(state: PipelineState) -> dict:
    """步驟 1：擷取資料"""
    print("  [Node] fetch_data")
    future = download_data(state["source_url"])
    return {"raw_data": future.result()}


def clean_data(state: PipelineState) -> dict:
    """步驟 2：清理資料"""
    print("  [Node] clean_data")
    raw = state["raw_data"]
    cleaned = raw.strip().upper()  # 確定性操作，不需要 task
    return {"cleaned_data": cleaned}


def analyze_data(state: PipelineState) -> dict:
    """步驟 3：分析資料（使用 LLM）"""
    print("  [Node] analyze_data")
    future = call_llm_for_analysis(state["cleaned_data"])
    return {"analysis": future.result()}


def generate_report(state: PipelineState) -> dict:
    """步驟 4：產生報告"""
    print("  [Node] generate_report")
    return {
        "report": (
            f"=== Report ===\n"
            f"Source: {state['source_url']}\n"
            f"Analysis: {state['analysis']}\n"
            f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    }


# === 建構 Graph ===
builder = StateGraph(PipelineState)

builder.add_node("fetch_data", fetch_data)
builder.add_node("clean_data", clean_data)
builder.add_node(
    "analyze_data",
    analyze_data,
    # LLM 呼叫可能暫時失敗，加入重試
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0),
)
builder.add_node("generate_report", generate_report)

builder.add_edge(START, "fetch_data")
builder.add_edge("fetch_data", "clean_data")
builder.add_edge("clean_data", "analyze_data")
builder.add_edge("analyze_data", "generate_report")
builder.add_edge("generate_report", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# === 執行 ===
if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("=== 執行 Pipeline ===")
    result = graph.invoke(
        {"source_url": "https://data.example.com/dataset-001"},
        config,
        durability="sync",  # 確保每一步都保存
    )
    print(f"\n最終報告:\n{result['report']}")

    # === 檢視 checkpoint 歷史 ===
    print("\n=== Checkpoint 歷史 ===")
    for state in graph.get_state_history(config):
        step = state.metadata.get("step", "?")
        next_nodes = state.next
        print(f"  Step {step}: next={next_nodes}")
