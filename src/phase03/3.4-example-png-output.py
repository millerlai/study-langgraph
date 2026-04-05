# 3.4 範例：PNG 渲染輸出（Mermaid.Ink）
# 展示將圖結構渲染為 PNG 圖片並儲存。
# 注意：需要網路連線（使用 Mermaid.Ink 線上 API 渲染）。

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1. 建構一個範例 Graph
class MyState(TypedDict):
    input: str
    output: str


def node_a(state: MyState) -> dict:
    return {"output": "A 處理完成"}


def node_b(state: MyState) -> dict:
    return {"output": "B 處理完成"}


def route(state: MyState) -> str:
    if len(state["input"]) > 10:
        return "node_b"
    return END


builder = StateGraph(MyState)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)

builder.add_edge(START, "node_a")
builder.add_conditional_edges("node_a", route, ["node_b", END])
builder.add_edge("node_b", END)

graph = builder.compile()


# 2. 方法一：儲存為 PNG 檔案
graph.get_graph().draw_mermaid_png(output_file_path="my_graph.png")
print("圖片已儲存為 my_graph.png")


# 3. 方法二：取得 PNG 的 bytes（適合在 Jupyter Notebook 顯示）
png_bytes = graph.get_graph().draw_mermaid_png()
print(f"PNG 大小: {len(png_bytes)} bytes")

# 在 Jupyter Notebook 中顯示：
# from IPython.display import Image, display
# display(Image(png_bytes))
