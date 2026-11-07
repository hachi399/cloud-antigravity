#!/bin/bash
set -euo pipefail

PROJECT_ID="overflowing-491800"
REGION="asia-northeast1"
BUCKET_NAME="antigravity-sandbox-overflowing-491800"
SA_NAME="sa-antigravity-runner"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================================="
echo "  Cloud Antigravity: GCP セキュリティ基盤セットアップ"
echo "=========================================================="
echo "[*] 対象プロジェクト: ${PROJECT_ID}"
echo "[*] リージョン:       ${REGION}"
echo "[*] 専用バケット名:   ${BUCKET_NAME}"

# 1. API 有効化
echo -e "\n[1/4] 必要な Google Cloud API を有効化中..."
gcloud services enable \
    run.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --project "${PROJECT_ID}"

# 2. 専用バケットの作成と隔離設定
echo -e "\n[2/4] 専用バケット (${BUCKET_NAME}) の作成と隔離..."
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud storage buckets create "gs://${BUCKET_NAME}" \
        --project "${PROJECT_ID}" \
        --location "${REGION}" \
        --uniform-bucket-level-access
    echo "  ✓ バケットを作成しました。"
else
    echo "  ✓ 既存バケットを確認しました。"
fi

# パブリック公開禁止
gcloud storage buckets update "gs://${BUCKET_NAME}" --public-access-prevention

# 3. 最小権限サービスアカウント
echo -e "\n[3/4] 最小権限サービスアカウントの作成..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${SA_NAME}" \
        --display-name="Antigravity Cloud Runner (Least Privilege)" \
        --project "${PROJECT_ID}"
    echo "  ✓ サービスアカウントを作成しました: ${SA_EMAIL}"
else
    echo "  ✓ 既存サービスアカウントを確認しました: ${SA_EMAIL}"
fi

# 4. バケット単位の IAM 権限バインド
echo -e "\n[4/4] バケット単位での最小権限バインド..."
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.objectAdmin"

# ログ出力権限
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter" \
    --condition=None >/dev/null 2>&1 || true

echo -e "\n[✓] GCP インフラのセットアップが完了しました。"
echo "    サービスアカウント: ${SA_EMAIL}"
echo "    隔離バケット:       gs://${BUCKET_NAME}"
