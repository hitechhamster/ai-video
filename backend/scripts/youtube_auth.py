"""一次性 YouTube 授权。浏览器点一次「同意」，令牌存本地，之后上传免手动。

用法（在 backend/ 下）：
    python scripts/youtube_auth.py
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.youtube_client import authorize

if __name__ == "__main__":
    authorize()
