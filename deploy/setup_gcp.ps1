<#
.SYNOPSIS
  Google Cloud 上に Antigravity 専用サンドボックス環境と最小権限 IAM を構築するスクリプト
#>

param (
    [string]$ProjectId = "",
    [string]$Region = "asia-northeast1",
    [string]$BucketName = "antigravity-sandbox-hachi399"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Cloud Antigravity: GCP セキュリティ基盤セットアップ" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null)
    if (-not $ProjectId) {
        Write-Error "GCP プロジェクトID が設定されていません。-ProjectId <ID> を指定するか、gcloud config set project <ID> を実行してください。"
        exit 1
    }
}

Write-Host "[*] 対象プロジェクト: $ProjectId" -ForegroundColor Green
Write-Host "[*] リージョン:       $Region" -ForegroundColor Green
Write-Host "[*] 専用バケット名:   $BucketName" -ForegroundColor Green

# 1. 必要な API の有効化
Write-Host "`n[1/4] 必要な Google Cloud API を有効化中..." -ForegroundColor Yellow
gcloud services enable `
    run.googleapis.com `
    storage.googleapis.com `
    cloudbuild.googleapis.com `
    secretmanager.googleapis.com `
    --project $ProjectId

# 2. 専用バケットの作成と隔離設定
Write-Host "`n[2/4] 専用バケット ($BucketName) の作成と鉄壁化..." -ForegroundColor Yellow
$bucketExists = gcloud storage buckets describe "gs://$BucketName" --project $ProjectId 2>$null
if (-not $bucketExists) {
    gcloud storage buckets create "gs://$BucketName" `
        --project $ProjectId `
        --location $Region `
        --uniform-bucket-level-access
    Write-Host "  ✓ バケットを作成しました。" -ForegroundColor Green
} else {
    Write-Host "  ✓ 既存バケットを確認しました。" -ForegroundColor Gray
}

# パブリック公開の完全禁止 (Public Access Prevention)
Write-Host "  -> パブリック公開防止 (Enforced) を適用中..." -ForegroundColor Gray
gcloud storage buckets update "gs://$BucketName" --public-access-prevention

# 3. 最小権限サービスアカウントの作成
Write-Host "`n[3/4] 最小権限サービスアカウント (sa-antigravity-runner) の作成..." -ForegroundColor Yellow
$saEmail = "sa-antigravity-runner@$ProjectId.iam.gserviceaccount.com"
$saExists = gcloud iam service-accounts describe $saEmail --project $ProjectId 2>$null
if (-not $saExists) {
    gcloud iam service-accounts create sa-antigravity-runner `
        --display-name="Antigravity Cloud Runner (Least Privilege)" `
        --project $ProjectId
    Write-Host "  ✓ サービスアカウントを作成しました: $saEmail" -ForegroundColor Green
} else {
    Write-Host "  ✓ 既存サービスアカウントを確認しました: $saEmail" -ForegroundColor Gray
}

# 4. バケット単位の IAM 権限バインド（※プロジェクト全体権限は一切与えない）
Write-Host "`n[4/4] バケット単位での最小権限バインド..." -ForegroundColor Yellow
gcloud storage buckets add-iam-policy-binding "gs://$BucketName" `
    --member="serviceAccount:$saEmail" `
    --role="roles/storage.objectAdmin"

# ログ出力権限（プロジェクトレベル）
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$saEmail" `
    --role="roles/logging.logWriter" `
    --condition=None 2>$null

Write-Host "`n[✓] GCP インフラのセットアップが完了しました。" -ForegroundColor Cyan
Write-Host "    サービスアカウント: $saEmail" -ForegroundColor White
Write-Host "    隔離バケット:       gs://$BucketName" -ForegroundColor White
