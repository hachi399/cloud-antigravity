<#
.SYNOPSIS
  Cloud Run へバックエンド API をビルド・デプロイするスクリプト
#>

param (
    [string]$ProjectId = "overflowing-491800",
    [string]$Region = "asia-northeast1",
    [string]$ServiceName = "cloud-antigravity-api",
    [string]$AllowedEmail = "yonghachi399@gmail.com",
    [string]$FrontendOrigin = "https://hachi399.github.io"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Cloud Antigravity: Cloud Run デプロイ" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null)
    if (-not $ProjectId) {
        Write-Error "GCP プロジェクトID が設定されていません。"
        exit 1
    }
}

$saEmail = "sa-antigravity-runner@$ProjectId.iam.gserviceaccount.com"

Push-Location (Join-Path $PSScriptRoot "..\backend")
try {
    Write-Host "[*] ソースから Cloud Run へのビルド＆デプロイを開始..." -ForegroundColor Yellow
    gcloud run deploy $ServiceName `
        --source . `
        --project $ProjectId `
        --region $Region `
        --service-account $saEmail `
        --allow-unauthenticated `
        --set-env-vars "ALLOWED_EMAIL=$AllowedEmail,FRONTEND_ORIGIN=$FrontendOrigin,SANDBOX_BUCKET_NAME=antigravity-sandbox-hachi399" `
        --min-instances 0 `
        --max-instances 2 `
        --memory 1Gi `
        --cpu 1

    Write-Host "`n[✓] Cloud Run デプロイが完了しました。" -ForegroundColor Green
    $serviceUrl = (gcloud run services describe $ServiceName --project $ProjectId --region $Region --format="value(status.url)")
    Write-Host "    サービス URL: $serviceUrl" -ForegroundColor Cyan
    Write-Host "    ※ frontend/app.js の CONFIG.apiBaseUrl にこの URL を設定してください。" -ForegroundColor Yellow
}
finally {
    Pop-Location
}
