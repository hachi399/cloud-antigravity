"""Cloud Run 上で稼働する Antigravity API サーバー
"""
import os
import uuid
from fastapi import FastAPI, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

from auth import verify_google_token
from storage import get_task_status, update_task_status, list_inbox_files
from agent import run_antigravity_task

app = FastAPI(
    title="Cloud Antigravity API",
    description="スマホから安全にクラウド上の Antigravity を駆動するゼロトラスト API",
    version="1.0.0"
)

# CORS 厳格設定
# お前の GitHub Pages ドメインと開発環境のみを許可
ALLOWED_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "https://hachi399.github.io"),
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# リクエスト / レスポンスモデル
class TaskCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="開発指示・依頼プロンプト")
    task_type: Optional[str] = Field("general", description="タスク分類 (code, doc, review 等)")

class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    summary: str
    updated_at: Optional[str] = None

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """生存監視エンドポイント"""
    return {"status": "ok", "service": "cloud-antigravity"}

@app.post(
    "/api/v1/tasks",
    response_model=TaskCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Tasks"]
)
def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(verify_google_token)
):
    """【認証必須】スマホから新しい開発指示を投入する。
    リクエストを受け付けたら即座に 202 を返し、バックグラウンドでエージェントを駆動する。
    """
    task_id = str(uuid.uuid4())
    
    # 初期ステータスを pending として GCS に書き込み
    update_task_status(task_id, "pending", summary="タスクを受け付けました。実行待機中...")

    # バックグラウンドで非同期実行
    background_tasks.add_task(
        run_antigravity_task,
        task_id=task_id,
        prompt=request.prompt,
        task_type=request.task_type
    )

    return TaskCreateResponse(
        task_id=task_id,
        status="pending",
        message="タスクを受領しました。エージェントが処理を開始します。"
    )

@app.get(
    "/api/v1/tasks/{task_id}/status",
    response_model=TaskStatusResponse,
    tags=["Tasks"]
)
def get_status(
    task_id: str,
    user_info: dict = Depends(verify_google_token)
):
    """【認証必須】タスクの現在の進捗ステータスを取得する。"""
    data = get_task_status(task_id)
    return TaskStatusResponse(
        task_id=data.get("task_id", task_id),
        status=data.get("status", "unknown"),
        summary=data.get("summary", ""),
        updated_at=data.get("updated_at")
    )

@app.get(
    "/api/v1/inbox",
    response_model=List[str],
    tags=["Storage"]
)
def get_inbox_files(user_info: dict = Depends(verify_google_token)):
    """【認証必須】PC から事前に投函されている素材ファイルの一覧を確認する。"""
    return list_inbox_files()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
