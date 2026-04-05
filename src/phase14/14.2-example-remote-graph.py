# 14.2 範例：RemoteGraph 完整使用
# 展示初始化、invoke、stream、state 管理、子圖嵌入
# 需要：pip install langgraph langgraph-sdk
# 需要：Agent Server 運行中（langgraph dev）

from langgraph.pregel.remote import RemoteGraph
from langgraph_sdk import get_sync_client
from langgraph.graph import StateGraph, MessagesState, START


# ============================================================
# 範例 1：基本使用 — invoke 和 stream
# ============================================================
def basic_usage():
    """透過 URL 初始化 RemoteGraph"""
    remote_graph = RemoteGraph(
        "agent",                           # graph 名稱或 assistant ID
        url="http://localhost:2024",       # 部署 URL
        # api_key="your-key"              # Cloud 部署需要
    )

    # invoke — 同步呼叫，等待完整結果
    result = remote_graph.invoke({
        "messages": [{"role": "user", "content": "你好！"}]
    })
    print(f"Invoke 結果: {result}")

    # stream — 串流取得結果
    for chunk in remote_graph.stream({
        "messages": [{"role": "user", "content": "天氣如何？"}]
    }):
        print(f"Stream chunk: {chunk}")


# ============================================================
# 範例 2：Thread 持久化
# ============================================================
def thread_persistence():
    """使用 thread 保持對話狀態"""
    url = "http://localhost:2024"
    sync_client = get_sync_client(url=url)
    remote_graph = RemoteGraph("agent", url=url)

    # 建立 thread
    thread = sync_client.threads.create()
    config = {"configurable": {"thread_id": thread["thread_id"]}}

    # 第一次對話
    result1 = remote_graph.invoke(
        {"messages": [{"role": "user", "content": "我叫小明"}]},
        config=config,
    )

    # 第二次對話（同一 thread，保持記憶）
    result2 = remote_graph.invoke(
        {"messages": [{"role": "user", "content": "我叫什麼名字？"}]},
        config=config,
    )

    # 取得 thread state
    state = remote_graph.get_state(config)
    print(f"Thread state: {state}")


# ============================================================
# 範例 3：作為子圖嵌入
# ============================================================
def subgraph_embedding():
    """將 RemoteGraph 作為子圖嵌入到父圖中"""
    remote_graph = RemoteGraph("agent", url="http://localhost:2024")

    # 建立父圖
    builder = StateGraph(MessagesState)
    # 直接將 RemoteGraph 加為節點
    builder.add_node("remote_agent", remote_graph)
    builder.add_edge(START, "remote_agent")

    parent_graph = builder.compile()

    # 執行父圖（會自動呼叫遠端 agent）
    result = parent_graph.invoke({
        "messages": [{"role": "user", "content": "幫我查天氣"}]
    })
    print(f"父圖結果: {result}")

    # 串流（含子圖輸出）
    for chunk in parent_graph.stream(
        {"messages": [{"role": "user", "content": "你好"}]},
        subgraphs=True,
    ):
        print(f"Chunk: {chunk}")


if __name__ == "__main__":
    basic_usage()
