# 14.3 範例：自訂認證處理器
# 驗證 API Key 並將使用者資訊傳入 Graph
# 需要：pip install langgraph-sdk
# 此檔案用於 Agent Server 的認證設定（langgraph.json 中的 auth.path）

from langgraph_sdk import Auth

auth = Auth()


def is_valid_key(api_key: str) -> bool:
    """驗證 API Key（實際應用中連接你的認證服務）"""
    valid_keys = {
        "key-user-001": "user_001",
        "key-user-002": "user_002",
    }
    return api_key in valid_keys


async def fetch_user_tokens(api_key: str) -> dict:
    """從 Secret Store 取得使用者的 tokens"""
    # 實際應用中應連接你的 secret manager
    return {
        "github_token": "ghp_xxx",
        "jira_token": "jira_xxx",
    }


@auth.authenticate
async def authenticate(headers: dict) -> Auth.types.MinimalUserDict:
    """
    認證處理器
    - 從 headers 取得 API key
    - 驗證有效性
    - 回傳使用者資訊（會成為 config["configurable"]["langgraph_auth_user"]）
    """
    api_key = headers.get(b"x-api-key")
    if isinstance(api_key, bytes):
        api_key = api_key.decode()

    if not api_key or not is_valid_key(api_key):
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    # 取得使用者專屬 tokens
    user_tokens = await fetch_user_tokens(api_key)

    # 回傳的 dict 會成為 langgraph_auth_user
    return {
        "identity": api_key,
        "github_token": user_tokens["github_token"],
        "jira_token": user_tokens["jira_token"],
    }
