# LangGraph 完整學習計畫

## Phase 1: 基礎概念

- [ ] **1.1 LangGraph 概觀** → [詳細筆記](src/phase1/1.1-langgraph-overview.md)
  - LangGraph 是什麼：低階的 stateful AI agent 編排框架
  - 與 LangChain 的關係與差異
  - 核心設計靈感：Google Pregel、Apache Beam、NetworkX
  - 適用場景：長時間執行的 AI agent、多步驟工作流

- [ ] **1.2 核心原語 (Core Primitives)** → [詳細筆記](src/phase1/1.2-core-primitives.md)
  - `StateGraph`：主要的圖抽象
  - `Node`：工作單元（LLM、函數、agent）
  - `Edge`：節點之間的連接（基本邊、條件邊）
  - `State`：節點之間傳遞的核心資料結構
  - `Channel`：State 中的個別欄位
  - `Reducer`：定義 State 更新如何合併
  - `END` 節點：標記執行終止
  - `Command`：結合控制流與 State 更新

- [ ] **1.3 第一個 Graph — Quickstart**
  - 建立基本聊天機器人
  - 加入工具（Tool Calling）
  - 加入記憶（Checkpointing）

---

## Phase 2: State 管理深入

- [ ] **2.1 State Schema 設計**
  - 使用 TypedDict 定義 State
  - 使用 Pydantic Model 定義 State
  - `MessagesState`：內建的訊息型 State Schema
  - Input / Output Schema 分離設計

- [ ] **2.2 Reducer 機制**
  - 預設 Reducer 行為
  - 自定義 Reducer 函數
  - 使用 `Annotated` 語法指定 Reducer
  - `Overwrite` 繞過 Reducer

- [ ] **2.3 Private State**
  - 節點之間的私有狀態傳遞
  - 不暴露給外部的內部資料

---

## Phase 3: 控制流與圖結構

- [ ] **3.1 基本控制流**
  - 線性序列（Sequential Steps）
  - 條件分支（Conditional Branching）
  - 迴圈（Loops）
  - 迴圈 + 分支組合

- [ ] **3.2 進階控制流**
  - 平行執行（Parallel Nodes）
  - 延遲執行（Deferred Nodes）
  - Map-Reduce 與 `Send` API
  - 遞迴限制（`GRAPH_RECURSION_LIMIT`）

- [ ] **3.3 Router 路由模式**
  - 基於條件的路由
  - LLM 驅動的動態路由

- [ ] **3.4 Graph 視覺化**
  - Mermaid 圖表輸出
  - PNG 渲染

---

## Phase 4: 持久化與 Checkpointing

- [ ] **4.1 Checkpointing 概念**
  - Thread（對話/工作階段）
  - Checkpoint（State 快照）
  - Super-step（單次執行 tick）

- [ ] **4.2 Checkpointer 實作**
  - `InMemorySaver`（開發用）
  - `SqliteSaver`（本地）
  - `PostgresSaver`（正式環境）
  - Checkpoint Namespace（父圖/子圖）

- [ ] **4.3 State 操作**
  - 取得目前 State
  - 查詢 State 歷史
  - 更新 State 建立新 Checkpoint
  - 失敗時的 Pending Writes 保留

---

## Phase 5: Human-in-the-Loop

- [ ] **5.1 中斷機制**
  - `interrupt()` 函數暫停執行
  - 靜態 Breakpoint
  - 動態 Breakpoint

- [ ] **5.2 人機協作模式**
  - 工具呼叫審核（Tool Call Approval）
  - 檢視並修改 Agent State
  - 從中斷點恢復執行
  - 子圖中的中斷處理

---

## Phase 6: Streaming

- [ ] **6.1 Stream 模式**
  - `values`：每步後完整 State 快照
  - `updates`：僅變更的 key
  - `messages`：LLM token + metadata
  - `custom`：透過 `get_stream_writer()` 自定義輸出
  - `checkpoints` / `tasks` / `debug` 模式

- [ ] **6.2 進階 Streaming**
  - 依節點過濾
  - 依 LLM 呼叫過濾（tags）
  - 子圖輸出（namespace）
  - 多模式同時串流
  - 非同步串流（`astream()`）

---

## Phase 7: 記憶系統

- [ ] **7.1 短期記憶**
  - 透過 Checkpointer 實現的工作記憶
  - 訊息裁剪（Trimming）
  - 訊息摘要（Summarizing）

- [ ] **7.2 長期記憶**
  - Memory Store（跨 Thread 狀態）
  - `InMemoryStore`
  - Namespace 組織
  - 語意搜尋（Embedding 整合）
  - `Store.put` / `Store.search`

---

## Phase 8: Time Travel

- [ ] **8.1 時間旅行功能**
  - 重播過去的執行
  - 從任意 Checkpoint 恢復
  - 新增步驟並重播歷史
  - 探索替代執行路徑
  - 除錯與問題回溯

---

## Phase 9: 子圖與模組化

- [ ] **9.1 Subgraph 設計**
  - 模組化圖組合
  - 父子圖共享 State Schema
  - 父子圖不同 State Schema
  - Checkpoint Namespace

- [ ] **9.2 子圖導航**
  - 透過 `Command` 導航到父圖節點
  - 子圖間的資料傳遞

---

## Phase 10: Multi-Agent 系統

- [ ] **10.1 多代理架構模式**
  - Supervisor 模式（中央協調者）
  - Swarm 模式（去中心化協調）
  - 階層式 Agent 團隊（Hierarchical）
  - Multi-Agent Network（路由到專家 Agent）

- [ ] **10.2 Agent 協作**
  - Agent Handoff（切換）
  - 分治法（Divide-and-Conquer）
  - `langgraph-supervisor` 函式庫
  - `langgraph-swarm` 函式庫

---

## Phase 11: Functional API

- [ ] **11.1 函數式 API**
  - `@entrypoint` 裝飾器
  - `@task` 裝飾器
  - Retry 與 Caching
  - Human-in-the-Loop（函數式版本）
  - 與 Graph API 的比較與選用時機

---

## Phase 12: 工具與整合

- [ ] **12.1 Tool Calling 模式**
  - 定義工具
  - 工具呼叫模式與錯誤處理
  - ReAct 模式（推理 + 行動迴圈）

- [ ] **12.2 MCP 整合**
  - Model Context Protocol 概念
  - 在 LangGraph 中使用 MCP Server

- [ ] **12.3 LLM 整合**
  - 整合不同 LLM 供應商
  - 自定義 LLM 整合（非 LangChain API）
  - Runtime 動態設定 LLM

---

## Phase 13: 進階應用模式

- [ ] **13.1 RAG Agent**
  - Agentic RAG
  - Adaptive RAG
  - Self-RAG（含本地 LLM）

- [ ] **13.2 Plan-and-Execute Agent**
  - 規劃與執行分離模式
  - 動態重新規劃

- [ ] **13.3 SQL Agent**
  - 資料庫查詢 Agent
  - 自然語言轉 SQL

- [ ] **13.4 Chatbot 模擬與評估**
  - 聊天機器人模擬測試
  - 基準測試（Benchmarking）

---

## Phase 14: 部署與平台

- [ ] **14.1 LangGraph Platform**
  - Platform 架構：Server、CLI、Studio、SDK
  - 應用程式結構（config、dependencies、graphs）

- [ ] **14.2 部署選項**
  - 本地伺服器（CLI + Studio）
  - Cloud 部署（從 GitHub repo）
  - Self-hosted（Kubernetes、ECS）
  - Docker 容器部署
  - `RemoteGraph`（連接已部署的 Graph）

- [ ] **14.3 營運功能**
  - Webhook（事件驅動整合）
  - Cron Job（排程執行）
  - 認證與授權（Authentication & Authorization）
  - Background Runs

---

## Phase 15: 可觀測性與除錯

- [ ] **15.1 LangSmith 整合**
  - Tracing（追蹤）
  - Evaluation（評估）
  - 執行路徑視覺化

- [ ] **15.2 LangGraph Studio**
  - 視覺化除錯 IDE
  - 連接本地或已部署的 Graph
  - State 轉換觀察

---

## Phase 16: 正式環境與錯誤處理

- [ ] **16.1 Durable Execution**
  - 故障持久化與自動恢復
  - 容錯與錯誤復原
  - 關鍵節點進度保存

- [ ] **16.2 錯誤處理**
  - 常見錯誤：`GRAPH_RECURSION_LIMIT`、`INVALID_CONCURRENT_GRAPH_UPDATE`
  - Retry Policy（重試策略）
  - 僅重試失敗的分支

- [ ] **16.3 序列化與安全**
  - `JsonPlusSerializer`
  - `EncryptedSerializer`（加密持久化）

---

## 參考資源

- [LangGraph 官方文件](https://langchain-ai.github.io/langgraph/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Academy（免費課程）](https://academy.langchain.com/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangGraph How-to Guides](https://langchain-ai.github.io/langgraph/how-tos/)
