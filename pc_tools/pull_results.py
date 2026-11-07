"""クラウド上の Antigravity (outbox/) から PC ローカルへ成果物を回収するスクリプト
"""
import os
import sys
import argparse
from pathlib import Path
from google.cloud import storage

BUCKET_NAME = os.getenv("SANDBOX_BUCKET_NAME", "antigravity-sandbox-hachi399")

def pull_results(dest_dir: str = "./cloud-results", task_id: str = None):
    """gs://<BUCKET_NAME>/outbox/ から成果物をローカルへ回収する"""
    dest = Path(dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    prefix = f"outbox/{task_id}/" if task_id else "outbox/"
    print(f"[*] GCS クライアント初期化中 (ソース: gs://{BUCKET_NAME}/{prefix})...")
    
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=prefix))
    except Exception as e:
        print(f"[Error] GCS 接続に失敗しました: {e}")
        sys.exit(1)

    if not blobs:
        print(f"[*] 回収対象の成果物は見つかりませんでした (prefix: {prefix})。")
        return

    print(f"[*] 回収対象: {len(blobs)} 件")
    for blob in blobs:
        if blob.name.endswith("/"):
            continue

        rel_path = blob.name.replace("outbox/", "")
        local_file = dest / rel_path
        local_file.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(str(local_file))
        print(f"  ↓ 回収完了: {blob.name} -> {local_file}")

    print(f"\n[✓] 成果物の回収が完了した。保存先: {dest}")
    print("    PC 上の各種ツールやテスト環境で自由に活用してくれ。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="クラウド Antigravity の outbox/ から成果物を回収")
    parser.add_argument("--dest", default="./cloud-results", help="回収先ローカルディレクトリ (デフォルト: ./cloud-results)")
    parser.add_argument("--task-id", default=None, help="特定のタスクIDのみ回収する場合に指定")
    args = parser.parse_args()

    pull_results(dest_dir=args.dest, task_id=args.task_id)
