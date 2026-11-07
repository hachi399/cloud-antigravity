"""Firebase Auth および Google ID トークン検証とゼロトラスト認可モジュール
"""
import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth as firebase_auth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Firebase Admin SDK の初期化
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "overflowing-491800")
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app(options={"projectId": PROJECT_ID})
    except Exception as e:
        print(f"Firebase Admin 初期化ログ: {e}")

security_scheme = HTTPBearer(auto_error=True)

# 認可する正規ユーザーのメールアドレス（環境変数またはデフォルト）
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL", "yonghachi399@gmail.com").strip().lower()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> dict:
    """Bearer トークンを暗号検証し、
    送信者が正当なユーザー（ホワイトリストのアドレス）か確認する。
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが提供されていません。",
        )

    user_email = ""
    is_email_verified = False
    decoded_info = {}

    # 1. まず Firebase ID トークンとして検証を試行（フロントエンドが Firebase Auth のため）
    try:
        decoded_info = firebase_auth.verify_id_token(token)
        user_email = decoded_info.get("email", "").strip().lower()
        is_email_verified = decoded_info.get("email_verified", False)
    except Exception as fb_err:
        # 2. フォールバック: 通常の Google OAuth2 トークンとして検証を試行
        try:
            request = google_requests.Request()
            decoded_info = id_token.verify_oauth2_token(token, request)
            user_email = decoded_info.get("email", "").strip().lower()
            is_email_verified = decoded_info.get("email_verified", False)
        except Exception as g_err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"無効な認証トークンです (Firebase: {str(fb_err)} / Google: {str(g_err)})",
            )

    # 送信元のメールアドレス検証（ホワイトリスト）
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="トークン内にメールアドレス情報が含まれていません。",
        )

    if not is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="メールアドレスが確認（Verify）されていません。",
        )

    if user_email != ALLOWED_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"アクセスが拒否されました。このアカウント ({user_email}) には操作権限がありません。",
        )

    return decoded_info
