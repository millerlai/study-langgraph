# 13.3 範例：基本 SQL Agent — 自然語言轉 SQL 查詢
# 使用 SQLite 範例資料庫（Chinook — 數位音樂商店）
# 需要設定 OPENAI_API_KEY 環境變數
# 需要安裝：pip install langgraph langchain-openai langchain-community

import os
import sqlite3
import pathlib
import requests
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.messages import AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

os.environ["OPENAI_API_KEY"] = "your-api-key"


# ---- 第一步：準備資料庫 ----
# 下載 Chinook 範例資料庫
db_path = pathlib.Path("Chinook.db")
if not db_path.exists():
    url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
    response = requests.get(url)
    if response.status_code == 200:
        db_path.write_bytes(response.content)
        print(f"已下載 {db_path}")

# 如果無法下載，建立一個簡單的範例資料庫
if not db_path.exists():
    conn = sqlite3.connect("Chinook.db")
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Artist (
            ArtistId INTEGER PRIMARY KEY,
            Name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Album (
            AlbumId INTEGER PRIMARY KEY,
            Title TEXT NOT NULL,
            ArtistId INTEGER REFERENCES Artist(ArtistId)
        );
        CREATE TABLE IF NOT EXISTS Genre (
            GenreId INTEGER PRIMARY KEY,
            Name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Track (
            TrackId INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            AlbumId INTEGER REFERENCES Album(AlbumId),
            GenreId INTEGER REFERENCES Genre(GenreId),
            Milliseconds INTEGER NOT NULL,
            UnitPrice REAL NOT NULL
        );
        INSERT OR IGNORE INTO Artist VALUES (1, 'AC/DC'), (2, 'Accept'), (3, 'Aerosmith');
        INSERT OR IGNORE INTO Genre VALUES (1, 'Rock'), (2, 'Jazz'), (3, 'Metal');
        INSERT OR IGNORE INTO Album VALUES (1, 'Highway to Hell', 1), (2, 'Back in Black', 1);
        INSERT OR IGNORE INTO Track VALUES
            (1, 'Highway to Hell', 1, 1, 215000, 0.99),
            (2, 'Back in Black', 2, 1, 255000, 0.99),
            (3, 'Hells Bells', 2, 3, 312000, 0.99);
    """)
    conn.commit()
    conn.close()
    print("已建立範例資料庫")

# 連接資料庫
db = SQLDatabase.from_uri("sqlite:///Chinook.db")
print(f"方言：{db.dialect}")
print(f"可用資料表：{db.get_usable_table_names()}")


# ---- 第二步：取得 SQL 工具 ----
model = init_chat_model("gpt-4o-mini", temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

print("\n可用工具：")
for tool in tools:
    print(f"  - {tool.name}: {tool.description[:80]}...")


# ---- 第三步：定義節點 ----
def list_tables(state: MessagesState):
    """第一步：列出所有資料表"""
    list_tables_tool = next(t for t in tools if t.name == "sql_db_list_tables")

    # 建立預定的 tool call
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "list_tables_call",
        "type": "tool_call",
    }
    tool_call_msg = AIMessage(content="", tool_calls=[tool_call])
    tool_response = list_tables_tool.invoke(tool_call)
    summary = AIMessage(content=f"可用的資料表：{tool_response.content}")

    print(f"  [列出資料表] {tool_response.content}")
    return {"messages": [tool_call_msg, tool_response, summary]}


# 取得 Schema 工具節點
get_schema_tool = next(t for t in tools if t.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")


def call_get_schema(state: MessagesState):
    """讓 LLM 選擇需要查看的資料表 Schema"""
    llm_with_tools = model.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# 執行查詢工具
run_query_tool = next(t for t in tools if t.name == "sql_db_query")
run_query_node = ToolNode([run_query_tool], name="run_query")


# 生成查詢
GENERATE_QUERY_PROMPT = """你是一個 SQL 查詢專家。
根據使用者問題和資料庫 Schema 生成正確的 {dialect} 查詢。

規則：
- 除非使用者指定數量，否則限制查詢結果最多 5 筆
- 按相關欄位排序以回傳最有意義的結果
- 只查詢需要的欄位，不要 SELECT *
- 絕對不要執行 INSERT、UPDATE、DELETE、DROP 等修改語句
""".format(dialect=db.dialect)


def generate_query(state: MessagesState):
    """生成 SQL 查詢"""
    system_msg = {"role": "system", "content": GENERATE_QUERY_PROMPT}
    llm_with_tools = model.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_msg] + state["messages"])
    return {"messages": [response]}


def should_continue(state: MessagesState):
    """判斷是否有查詢需要執行"""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "run_query"
    return "__end__"


# ---- 第四步：組裝圖 ----
workflow = StateGraph(MessagesState)

workflow.add_node("list_tables", list_tables)
workflow.add_node("call_get_schema", call_get_schema)
workflow.add_node("get_schema", get_schema_node)
workflow.add_node("generate_query", generate_query)
workflow.add_node("run_query", run_query_node)

# 固定流程：列表 -> 取 Schema -> 生成查詢
workflow.add_edge(START, "list_tables")
workflow.add_edge("list_tables", "call_get_schema")
workflow.add_edge("call_get_schema", "get_schema")
workflow.add_edge("get_schema", "generate_query")

# 條件邊：生成查詢後可能執行或結束
workflow.add_conditional_edges(
    "generate_query",
    should_continue,
    {"run_query": "run_query", "__end__": END},
)
# 查詢結果回到生成節點（可以繼續問或結束）
workflow.add_edge("run_query", "generate_query")

graph = workflow.compile()


# ---- 第五步：測試 ----
if __name__ == "__main__":
    print("\n=== SQL Agent 測試 ===\n")

    question = "哪個音樂類型的曲目平均最長？"
    print(f"問題：{question}\n")

    for step in graph.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        last_msg = step["messages"][-1]
        if hasattr(last_msg, "content") and last_msg.content:
            print(f"  {last_msg.content[:200]}")
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                print(f"  [工具呼叫] {tc['name']}: {tc['args']}")
