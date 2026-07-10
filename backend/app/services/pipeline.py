import asyncio
import base64
import traceback
from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.models import Job, Project, Segment
from app.providers.image.seedream import SeedreamImageProvider
from app.providers.tts.minimax import MiniMaxTTSProvider
from app.services import audio_align, jianying_draft, scene_prompt
from app.services.script_splitter import split_script

tts_provider = MiniMaxTTSProvider()
image_provider = SeedreamImageProvider()


def _project_dir(project_id: str) -> Path:
    path = settings.storage_path / "projects" / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _to_data_uri(image_bytes: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def run_generation(job_id: str) -> None:
    """同步函数，供 FastAPI BackgroundTasks 在线程池中执行。"""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        project = db.get(Project, job.project_id)
        if project is None:
            job.status = "failed"
            job.error_message = "项目不存在"
            db.commit()
            return

        job.status = "running"
        job.current_step = "拆分脚本"
        db.commit()

        texts = split_script(project.script)
        if not texts:
            raise ValueError("脚本为空，无法生成")

        # 重新生成时清掉上一轮遗留的分镜段落，避免新旧数据混在一起
        db.query(Segment).filter(Segment.project_id == project.id).delete()
        db.commit()

        project_dir = _project_dir(project.id)
        segments = [
            Segment(project_id=project.id, index=i, text=text) for i, text in enumerate(texts)
        ]
        db.add_all(segments)
        db.commit()

        style = project.style
        negative_prompt = "，".join(
            p for p in [style.negative_prompt, "文字，字幕，汉字，英文单词，水印"] if p
        )

        # 整段脚本一次性合成配音，保留原有的标点/换行停顿节奏，避免逐句合成的割裂感
        job.current_step = "整段配音合成中"
        db.commit()
        audio_result = asyncio.run(tts_provider.synthesize(project.script, project.voice_id))
        voice_path = project_dir / "full_voice.mp3"
        voice_path.write_bytes(audio_result.audio_bytes)
        total_duration = audio_result.duration_seconds or audio_align.probe_duration(voice_path)

        # 用静音检测把整段配音切回每句的时间线（检测点不够时会自动降级为按字数比例切）
        job.current_step = "按停顿切分句子时间线"
        db.commit()
        boundaries = audio_align.split_by_silence(voice_path, texts)
        for segment, (start, end) in zip(segments, boundaries):
            segment.start_offset = start
            segment.duration = end - start
        db.commit()

        # 先生成一张角色定妆图，后面每句配图都拿它当参考图，锁定跨分镜的角色一致性
        job.current_step = "生成角色定妆图"
        db.commit()
        character_prompt, _ = scene_prompt.build_character_prompt(style)
        character_result = asyncio.run(
            image_provider.generate(character_prompt, negative_prompt=negative_prompt)
        )
        character_ref_path = project_dir / "character_ref.png"
        character_ref_path.write_bytes(character_result.image_bytes)
        project.character_ref_path = str(character_ref_path)
        db.commit()
        character_ref_data_uri = _to_data_uri(character_result.image_bytes)

        total_steps = len(segments) + 1  # +1 for final draft assembly
        for i, segment in enumerate(segments):
            job.current_step = f"第 {i + 1}/{len(segments)} 段：生成结构化场景提示词"
            db.commit()

            try:
                img_prompt, video_prompt_text = asyncio.run(
                    scene_prompt.build_scene_prompt(segment.text, style)
                )
                segment.video_prompt = video_prompt_text
            except Exception:  # noqa: BLE001
                # 结构化提示词生成失败时优雅降级，不影响整体生成
                print(f"[scene_prompt DEBUG] failed:\n{traceback.format_exc()}")
                img_prompt = (
                    f"{style.prompt_suffix}\n"
                    f"为下面这句旁白配一张对应场景的插画，画面中禁止出现任何文字、字幕、汉字或水印：{segment.text}"
                )
            db.commit()

            job.current_step = f"第 {i + 1}/{len(segments)} 段：画面生成中"
            db.commit()

            image_result = asyncio.run(
                image_provider.generate(
                    img_prompt,
                    negative_prompt=negative_prompt,
                    reference_image_url=character_ref_data_uri,
                )
            )
            image_path = project_dir / f"segment_{i}.png"
            image_path.write_bytes(image_result.image_bytes)
            segment.image_path = str(image_path)
            segment.status = "done"
            db.commit()

            job.progress = (i + 1) / total_steps
            db.commit()

        job.current_step = "装配剪映草稿"
        db.commit()
        draft_name = jianying_draft.build_draft(
            project, segments, voice_path, total_duration, effect_preset=project.effect_preset
        )

        project.video_path = draft_name
        project.status = "succeeded"
        job.progress = 1.0
        job.status = "succeeded"
        job.current_step = "完成"
        db.commit()

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.get(Job, job_id)
        if job is not None:
            job.status = "failed"
            job.error_message = f"{exc}\n{traceback.format_exc()[-1500:]}"
            db.commit()
        project = db.get(Project, job.project_id) if job else None
        if project is not None:
            project.status = "failed"
            db.commit()
    finally:
        db.close()
