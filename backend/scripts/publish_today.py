r"""把剪映刚导出的 mp4 传到 YouTube。

用法（在 backend/ 下）：
    python scripts/publish_today.py                  # 抓 youtube_export_dir 里最新的 mp4
    python scripts/publish_today.py path\to\clip.mp4  # 指定某个 mp4

匹配逻辑：剪映默认导出文件名 = 草稿名，据此反查项目、读它的 youtube_meta.json 拿标题/描述。
匹配不到就退回用文件名当标题、隐私用默认值，仍然能传。
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.db import SessionLocal
from app.models import Project

from scripts import youtube_client


def _newest_mp4(folder: Path) -> Path | None:
    mp4s = list(folder.glob("*.mp4"))
    if not mp4s:
        return None
    return max(mp4s, key=lambda p: p.stat().st_mtime)


def _meta_for(video_path: Path) -> dict | None:
    """按导出文件名（=草稿名）反查项目，读它的 youtube_meta.json；匹配不到返回 None。"""
    stem = video_path.stem  # 例如 "BaZi and Feng Shui_4dfddce7"
    db = SessionLocal()
    project = db.query(Project).filter(Project.video_path == stem).first()
    db.close()
    if project is not None:
        meta_file = settings.storage_path / "projects" / project.id / "youtube_meta.json"
        if meta_file.exists():
            return json.loads(meta_file.read_text(encoding="utf-8"))
    return None


def main() -> None:
    explicit = len(sys.argv) > 1
    if explicit:
        video_path = Path(sys.argv[1])
        if not video_path.is_file():
            raise SystemExit(f"文件不存在：{video_path}")
    else:
        folder = Path(settings.youtube_export_dir)
        if not folder.is_dir():
            raise SystemExit(f"导出目录不存在：{folder}（在 .env 里设 youtube_export_dir）")
        found = _newest_mp4(folder)
        if found is None:
            raise SystemExit(f"{folder} 里没有 mp4，先在剪映导出到这里")
        video_path = found

    meta = _meta_for(video_path)
    if meta is None:
        if not explicit:
            # 文件夹扫描时匹配不到项目就中止，避免误发无关视频
            raise SystemExit(
                f"最新的 mp4「{video_path.name}」匹配不到项目元数据。\n"
                f"确认是从本工具生成的草稿导出的、且没改文件名。\n"
                f"要发指定文件用：python scripts/publish_today.py <路径>"
            )
        # 显式指定文件时，允许用文件名当标题兜底上传
        print(f"⚠️ 没匹配到项目元数据，用文件名当标题、默认隐私上传")
        meta = {
            "title": video_path.stem,
            "description": "",
            "tags": [],
            "privacy": settings.youtube_privacy,
        }
    print(f"上传：{video_path.name}")
    print(f"标题：{meta['title']}")
    print(f"隐私：{meta.get('privacy', settings.youtube_privacy)}")

    url = youtube_client.upload(
        video_path,
        title=meta["title"],
        description=meta.get("description", ""),
        tags=meta.get("tags", []),
        privacy=meta.get("privacy", settings.youtube_privacy),
    )
    print(f"\n✅ 已上传：{url}")


if __name__ == "__main__":
    main()
