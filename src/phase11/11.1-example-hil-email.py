# 11.1 範例：函數式 API 的 Human-in-the-Loop 工作流
# 示範使用 interrupt() 暫停工作流等待人類輸入，再以 Command(resume=...) 恢復

import uuid
from langgraph.func import entrypoint, task
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

@task
def draft_email(topic: str) -> str:
    """草擬一封電子郵件"""
    return f"親愛的客戶，\n\n關於{topic}，我們想通知您最新進展...\n\n此致敬禮"

@task
def send_email(content: str, approved: bool) -> str:
    """根據審核結果發送或取消"""
    if approved:
        return f"郵件已發送:\n{content}"
    else:
        return "郵件已取消"

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def email_workflow(topic: str) -> dict:
    """郵件草擬 → 人工審核 → 發送/取消"""
    # Step 1: 自動草擬
    draft = draft_email(topic).result()

    # Step 2: 暫停等待人工審核
    review = interrupt({
        "draft": draft,
        "action": "請審核此郵件內容，回覆 true（核准）或 false（拒絕）"
    })

    # Step 3: 根據審核結果處理
    result = send_email(draft, review).result()

    return {"draft": draft, "review_result": review, "outcome": result}

# ============================================================
# 執行工作流
# ============================================================
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# 第一階段：啟動工作流 → 自動草擬後暫停
print("=== 啟動工作流 ===")
for item in email_workflow.stream("產品更新", config):
    print(item)
# 輸出:
# {'draft_email': '親愛的客戶，\n\n關於產品更新，...'}
# {'__interrupt__': (Interrupt(value={'draft': '...', 'action': '...'}),)}

print("\n=== 人工審核後恢復 ===")
# 第二階段：人工核准後恢復
for item in email_workflow.stream(Command(resume=True), config):
    print(item)
# 輸出:
# {'send_email': '郵件已發送:\n親愛的客戶，...'}
# {'email_workflow': {'draft': '...', 'review_result': True, 'outcome': '郵件已發送:...'}}
