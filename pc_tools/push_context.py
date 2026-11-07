"""自宅 PC からクラウド上の Antigravity (inbox/) へ一方通行で素材・コンテキストを投函するスクリプト
"""
import os
import sys
import argparse
from pathlib import Path
from google.cloud import storage

BUCKET_NAME = os.getenv("SANDBOX_BUCKET_NAME", "antigravity-sandbox-overflowing-491800")

def push_context(source_path: str, clean_remote: bool = False):
    """指定したファイルまたはディレクトリを gs://<BUCKET_NAME>/inbox/ へ投函する"""
    src = Path(source_path).resolve()
    if not src.exists():
        print(f"[Error] 指定されたパスが存在しません: {src}")
        sys.exit(1)

    print(f"[*] GCS クライアント初期化中 (ターゲット: gs://{BUCKET_NAME}/inbox/)...")
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
    except Exception as e:
        print(f"[Error] GCS 認証に失敗しました。`gcloud auth application-default login` を実行してください: {e}")
        sys.exit(1)

    if clean_remote:
        print("[*] 既存の inbox/ をクリーンアップ中...")
        blobs = bucket.list_blobs(prefix="inbox/")
        for b in blobs:
            b.delete()
        print("  ✓ クリーンアップ完了")

    files_to_upload = []
    if src.is_file():
        files_to_upload.append((src, f"inbox/{src.name}"))
    else:
        for f in src.rglob("*"):
            if f.is_file() and not any(part.startswith(".") for part in f.parts):
                rel = f.relative_to(src)
                remote_name = f"inbox/{rel.as_posix()}"
                files_to_upload.append((f, remote_name))

    print(f"[*] アップロード対象: {len(files_to_upload)} 件")
    for local_file, remote_blob_name in files_to_upload:
        blob = bucket.blob(remote_blob_name)
        blob.upload_from_filename(str(local_file))
        print(f"  ↑ 投函完了: {local_file.name} -> {remote_blob_name}")

    print("\n[✓] すべてのコンテキストをクラウドの専用バケットへ投函した。")
    print("    外出先でスマホからタスクを発令すれば、エージェントがこれらの素材を参照して動く。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PC からクラウド Antigravity の inbox/ へデータを一方通行で投函")
    parser.add_argument("path", help="投函したいファイルまたはフォルダのパス")
    parser.add_argument("--clean", action="store_true", help="投函前に既存の inbox を空にする")
    args = parser.parse_args()

    push_context(args.path, clean_remote=args.clean)
