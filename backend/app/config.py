from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    minimax_api_host: str = "https://api.minimaxi.com"
    minimax_api_key: str = ""
    minimax_text_model: str = "MiniMax-M2.5"

    ark_api_key: str = ""
    ark_image_model: str = "doubao-seedream-4-5-251128"

    # Google Gemini (Nano Banana)：画风需要画面里出现准确英文文字时用它，Seedream 画不出可读文字
    # 注：不要随手换成 gemini-3.1-flash-image，实测它偏写实、英文反而会拼错
    gemini_api_key: str = ""
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_text_model: str = "gemini-2.5-flash"

    # OpenRouter：生图走它代理的 gemini-2.5-flash-image；它没有可用的TTS，所以配音回落到 MiniMax
    openrouter_api_key: str = ""
    openrouter_image_model: str = "google/gemini-2.5-flash-image"
    openrouter_text_model: str = "google/gemini-2.5-flash"

    # 备用：通义万相适配器仍保留在 providers/image/tongyi_wanxiang.py，如需切换回去要配这个
    dashscope_api_key: str = ""

    caption_font_path: str = "C:/Windows/Fonts/msyhbd.ttc"

    # 剪映草稿文件夹（剪映App "全局设置 -> 草稿位置" 里能查到自己的实际路径）
    jianying_drafts_dir: str = (
        r"C:\Users\22460\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    )
    canvas_width: int = 1080
    canvas_height: int = 1920

    storage_dir: str = "storage"

    # ── 每日自动出片 + YouTube 上传 ──────────────────────────────
    # 每天用哪个模板出片（按模板名找，改名了记得同步）
    daily_template_name: str = "长衫先生"
    # 剪映导出 mp4 落地的文件夹——publish 时从这里抓最新的 mp4。
    # 用一个"专用"子文件夹，别用通用的"视频"目录，免得抓到无关的录屏误发。
    # 在剪映里把导出目录固定到这里。
    youtube_export_dir: str = r"D:\GA4数据分析\video_draft"
    # 上传后的默认隐私：private / unlisted / public
    youtube_privacy: str = "private"
    # OAuth 凭据与令牌（放 backend/ 下，已被 .gitignore 排除）
    youtube_client_secret_file: str = "client_secret.json"
    youtube_token_file: str = "youtube_token.json"

    @property
    def storage_path(self) -> Path:
        path = BACKEND_DIR / self.storage_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
