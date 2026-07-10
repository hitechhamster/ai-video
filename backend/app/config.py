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

    @property
    def storage_path(self) -> Path:
        path = BACKEND_DIR / self.storage_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
