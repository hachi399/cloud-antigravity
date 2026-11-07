# Cloud Antigravity (ゼロトラスト・サーバーレス常駐型エージェント)

自宅 PC を常時起動することなく、外出先のスマートフォンからセキュアに AI エージェント（Antigravity）へ開発・調査タスクを委譲・実行させるためのサーバーレス・アーキテクチャ。

## 概要

- **Frontend**: GitHub Pages（静的 Web UI、スマホ PWA 最適化）
- **Backend**: Google Cloud Run（FastAPI + Antigravity Python SDK、サーバーレス稼働）
- **Storage**: Google Cloud Storage（`antigravity-sandbox` 隔離バケット、5TB プラン環境）
- **Security**: Google Identity Platform / Firebase Auth によるゼロトラスト本人認証（JWT 暗号検証）
- **PC 連携**: 自宅 PC からクラウドの `inbox/` への非対称一方通行データ投函

---

## ディレクトリ構成

```
cloud-antigravity/
├── frontend/                # GitHub Pages でホストする静的サイト (Web UI)
│   ├── index.html          # モバイル対応 UI (Google 認証 + タスク送信)
│   ├── app.js              # Firebase Auth 連携 + API 通信
│   └── style.css           # ダークモードテーマ
├── backend/                 # Google Cloud Run 上で動く API
│   ├── Dockerfile          # コンテナ定義
│   ├── requirements.txt    # 依存ライブラリ
│   ├── main.py             # FastAPI エントリポイント (CORS, ルーティング)
│   ├── auth.py             # Google JWT トークン検証 & メールホワイトリスト
│   ├── agent.py            # Antigravity Python SDK 実行ラッパー
│   └── storage.py          # GCS サンドボックスバケット操作
├── pc_tools/                # 自宅 PC からの安全な一方通行連携スクリプト
│   ├── push_context.py     # PC の素材・コードを gs://.../inbox/ へ投函
│   └── pull_results.py     # クラウド成果物を gs://.../outbox/ から回収
├── deploy/                  # 自動構築・デプロイスクリプト
│   ├── setup_gcp.ps1       # バケット・IAM・サービスアカウント自動構築
│   └── deploy_cloud_run.ps1# Cloud Run ビルド＆デプロイ
└── README.md
```

---

## セットアップ手順

### 1. GCP インフラ基盤の自動構築 (自宅 PC から実行)
```powershell
.\deploy\setup_gcp.ps1 -ProjectId "YOUR_GCP_PROJECT_ID"
```

### 2. Cloud Run へのバックエンドデプロイ
```powershell
.\deploy\deploy_cloud_run.ps1 -ProjectId "YOUR_GCP_PROJECT_ID"
```
※ デプロイ完了時に表示されるサービス URL（`https://...a.run.app`）をメモします。

### 3. フロントエンドの設定 & GitHub Pages 公開
1. `frontend/app.js` を開き、以下の2箇所をお前の値に書き換えます：
   - `CONFIG.apiBaseUrl`: Step 2 で取得した Cloud Run サービス URL
   - `CONFIG.firebaseConfig`: Firebase Console で Web アプリを作成した際の設定値
2. GitHub にリポジトリを作成し、`frontend/` 配下を GitHub Pages として公開します。

---

## 日常の運用フロー

1. **外出前（自宅 PC）**:
   ```bash
   python pc_tools/push_context.py ./my-project/
   ```
   PC の作業ファイルやコンテキストをクラウドの `inbox/` に一方通行で投函し、PC をシャットダウン。
2. **出先・移動中（スマホ）**:
   - スマホで GitHub Pages を開き、Google アカウントでログイン。
   - 指示（プロンプト）を入力して発令。エージェントが自律処理してクラウドに保存。
3. **帰宅後（自宅 PC）**:
   ```bash
   python pc_tools/pull_results.py
   ```
   クラウドの成果物を PC に安全に回収し、ローカルのツールや環境で確認・活用。
