FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存パッケージの導入
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 依存ライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート設定 (Cloud Run の標準 PORT 環境変数)
ENV PORT=8080
EXPOSE 8080

# Uvicorn による起動
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
