"""Google Cloud Storage 専用サンドボックス操作モジュール
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from google.cloud import storage

BUCKET_NAME = os.getenv("SANDBOX_BUCKET_NAME", "antigravity-sandbox-overflowing-491800")

def _get_storage_client() -> storage.Client:
    return storage.Client()

def list_inbox_files() -> List[str]:
    """PC から投函された inbox 配下のファイル一覧を取得"""
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="inbox/")
    return [blob.name.replace("inbox/", "") for blob in blobs if not blob.name.endswith("/")]

def read_inbox_context() -> str:
    """inbox/ に存在するテキスト・コードファイルを結合してエージェントのコンテキストとして読み出す"""
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="inbox/")

    context_parts = []
    for blob in blobs:
        if blob.name.endswith("/") or blob.size > 2 * 1024 * 1024:  # 2MB超はスキップ
            continue
        try:
            content = blob.download_as_text()
            context_parts.append(f"--- [File: {blob.name}] ---\n{content}\n")
        except Exception:
            # バイナリ等の場合はスキップ
            continue

    return "\n".join(context_parts)

def update_task_status(task_id: str, status: str, summary: Optional[str] = None):
    """タスクの状態（pending, running, completed, failed）を status.json として保存"""
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"outbox/{task_id}/status.json")

    status_data = {
        "task_id": task_id,
        "status": status,
        "summary": summary or "",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    blob.upload_from_string(json.dumps(status_data, ensure_ascii=False, indent=2), content_type="application/json")

def get_task_status(task_id: str) -> Dict[str, Any]:
    """タスクの状態を取得"""
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"outbox/{task_id}/status.json")

    if not blob.exists():
        return {"task_id": task_id, "status": "unknown", "summary": "タスクが見つかりません。"}

    data = json.loads(blob.download_as_text())
    return data

def save_task_result(task_id: str, prompt: str, result_text: str, files_generated: Dict[str, str]):
    """Antigravity の実行成果物を outbox 配下に保存"""
    client = _get_storage_client()
    bucket = client.bucket(BUCKET_NAME)

    # 1. 成果物サマリー (result.md)
    summary_blob = bucket.blob(f"outbox/{task_id}/result.md")
    summary_content = f"# タスク実行成果物: {task_id}\n\n## プロンプト\n{prompt}\n\n## 実行結果\n{result_text}\n"
    summary_blob.upload_from_string(summary_content, content_type="text/markdown")

    # 2. 個別生成ファイル群
    for file_name, content in files_generated.items():
        file_blob = bucket.blob(f"outbox/{task_id}/artifacts/{file_name}")
        file_blob.upload_from_string(content, content_type="text/plain")

    # 3. 完了ステータスの更新
    update_task_status(task_id, "completed", summary="タスクが正常に完了し、成果物が保存されました。")
