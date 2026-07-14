"""生成"今天的视频"：选题 → 写稿 → 出图配音 → 剪映草稿，并把 YouTube 元数据存到项目里。

用法（在 backend/ 下）：
    python scripts/make_today.py                # 题库自动轮换取下一个选题
    python scripts/make_today.py "your topic"   # 指定一个临时选题

跑完会打印草稿名，去剪映打开这个草稿、导出到 youtube_export_dir，再用 publish_today.py 上传。
"""

import json
import sys
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
# 允许 `python scripts/make_today.py` 直接跑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.db import SessionLocal
from app.models import Job, Project, Template
from app.services.pipeline import run_generation

from scripts import daily_content


def main() -> None:
    topic_arg = sys.argv[1] if len(sys.argv) > 1 else None

    db = SessionLocal()
    template = (
        db.query(Template).filter(Template.name == settings.daily_template_name).first()
    )
    if template is None:
        raise SystemExit(f"找不到模板「{settings.daily_template_name}」，先在 seed/前端里建好它")

    print(f"选题中…（模板：{template.name}）")
    topic_index, content = daily_content.generate(topic_arg)
    print(f"选题：{content.topic}")
    print(f"标题：{content.title}")

    project = Project(
        id=uuid.uuid4().hex,
        name=content.title[:80],
        script=content.script,
        style_id=template.style_id,
        voice_id=template.voice_id,
        music_id=template.music_id,
        effect_preset_id=template.effect_preset_id,
        template_id=template.id,
        status="draft",
    )
    db.add(project)
    db.flush()
    job = Job(id=uuid.uuid4().hex, project_id=project.id, status="pending")
    db.add(job)
    db.commit()
    project_id = project.id
    db.close()

    print("生成中（出图 + 配音 + 装配草稿）…")
    run_generation(job.id)

    db = SessionLocal()
    job = db.get(Job, job.id)
    project = db.get(Project, project_id)
    if job.status != "succeeded":
        raise SystemExit(f"生成失败：{job.current_step}\n{job.error_message}")

    # 把 YouTube 元数据写到项目目录，publish 时按草稿名反查读取
    meta = {
        "draft_name": project.video_path,
        "title": content.title,
        "description": f"{content.description}\n\n{' '.join(content.hashtags)}".strip(),
        "tags": [h.lstrip("#") for h in content.hashtags],
        "privacy": settings.youtube_privacy,
        "topic": content.topic,
    }
    project_dir = settings.storage_path / "projects" / project.id
    (project_dir / "youtube_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    daily_content.commit_topic(topic_index)
    db.close()

    print("\n✅ 生成完成")
    print(f"草稿名：{meta['draft_name']}")
    print("下一步：在剪映里打开这个草稿 → 导出到 " + settings.youtube_export_dir)
    print("导出后运行：python scripts/publish_today.py")


if __name__ == "__main__":
    main()
