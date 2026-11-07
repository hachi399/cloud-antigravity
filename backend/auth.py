"""Google ID トークン検証とゼロトラスト認可モジュール
"""
import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

security_scheme = HTTPBearer(auto_error=True)

# 認可する正規ユーザーのメールアドレス（環境変数またはデフォルト）
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL", "yonghachi399@gmail.com").strip().lower()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def verify_google_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> dict:
    """Bearer トークンを Google の公開鍵で暗号検証し、
    送信者が正当なユーザー（ホワイトリストのアドレス）か確認する。
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが提供されていません。",
        )

    try:
        # Google 公開鍵で暗号署名と有効期限を検証
        request = google_requests.Request()
        # GOOGLE_CLIENT_ID が指定されていれば aud を検証、未指定なら署名のみ検証
        audience = GOOGLE_CLIENT_ID if GOOGLE_CLIENT_ID else None
        id_info = id_token.verify_oauth2_token(token, request, audience=audience)

        # 送信元のメールアドレス検証（ホワイトリスト）
        user_email = id_info.get("email", "").strip().lower()
        is_email_verified = id_info.get("email_verified", False)

        if not is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="メールアドレスが確認（Verify）されていません。",
            )

        if user_email != ALLOWED_EMAIL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"アクセスが拒否されました。このアカウント ({user_email}) には権限がありません。",
            )

        return id_info

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"無効な Google 認証トークンです: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"トークン検証処理中にエラーが発生しました: {str(e)}",
        )
