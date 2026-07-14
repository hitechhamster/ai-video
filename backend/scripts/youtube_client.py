"""YouTube Data API v3 封装：一次性授权 + 上传视频。

Google 库是惰性导入的——没装或没授权时，脚本不会因为 import 就崩，
而是给出清楚的安装/授权指引。
"""

from pathlib import Path

from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

_SETUP_HINT = """
还没准备好 YouTube 上传，缺一次性设置：

1) 装依赖：
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

2) 到 Google Cloud 建项目 → 启用「YouTube Data API v3」→ 建 OAuth 客户端(桌面应用)
   → 下载 client_secret.json，放到 backend/ 下（文件名对应 settings.youtube_client_secret_file）
   → OAuth 同意屏幕发布到 In production（避免刷新令牌 7 天过期）

3) 授权一次：
   python scripts/youtube_auth.py
"""


def _client_secret_path() -> Path:
    return BACKEND_DIR / settings.youtube_client_secret_file


def _token_path() -> Path:
    return BACKEND_DIR / settings.youtube_token_file


def authorize() -> None:
    """一次性 OAuth：打开浏览器让用户同意，令牌存到 youtube_token_file。"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(_SETUP_HINT) from exc

    secret = _client_secret_path()
    if not secret.exists():
        raise SystemExit(f"缺少 {secret.name}（放到 backend/ 下）。\n{_SETUP_HINT}")

    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0)
    _token_path().write_text(creds.to_json(), encoding="utf-8")
    print(f"✅ 授权成功，令牌已存到 {_token_path().name}")


def _load_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token = _token_path()
    if not token.exists():
        raise SystemExit(f"还没授权（缺 {token.name}）。先跑：python scripts/youtube_auth.py")

    creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise SystemExit(f"令牌失效，重新授权：python scripts/youtube_auth.py")
    return creds


def upload(video_path: Path, title: str, description: str, tags: list[str], privacy: str) -> str:
    """上传一个 mp4，返回视频 URL。缺依赖/未授权会抛 SystemExit 并给指引。"""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise SystemExit(_SETUP_HINT) from exc

    creds = _load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy if privacy in ("private", "unlisted", "public") else "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  上传中 {int(status.progress() * 100)}%")
    video_id = response["id"]
    return f"https://youtube.com/shorts/{video_id}"
