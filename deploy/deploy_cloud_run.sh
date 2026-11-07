#!/bin/bash
set -euo pipefail

PROJECT_ID="overflowing-491800"
REGION="asia-northeast1"
SERVICE_NAME="cloud-antigravity-api"
ALLOWED_EMAIL="yonghachi399@gmail.com"
FRONTEND_ORIGIN="https://hachi399.github.io"
BUCKET_NAME="antigravity-sandbox-overflowing-491800"
SA_EMAIL="sa-antigravity-runner@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================================="
echo "  Cloud Antigravity: Cloud Run デプロイ"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../backend"

echo "[*] ソースから Cloud Run へのビルド＆デプロイを開始..."
gcloud run deploy "${SERVICE_NAME}" \
    --source . \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --service-account "${SA_EMAIL}" \
    --allow-unauthenticated \
    --set-env-vars "ALLOWED_EMAIL=${ALLOWED_EMAIL},FRONTEND_ORIGIN=${FRONTEND_ORIGIN},SANDBOX_BUCKET_NAME=${BUCKET_NAME}" \
    --min-instances 0 \
    --max-instances 2 \
    --memory 1Gi \
    --cpu 1

echo -e "\n[✓] Cloud Run デプロイが完了しました。"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project "${PROJECT_ID}" --region "${REGION}" --format="value(status.url)")
echo "    サービス URL: ${SERVICE_URL}"
echo "    ※ frontend/app.js の CONFIG.apiBaseUrl にこの URL を設定してください。"
