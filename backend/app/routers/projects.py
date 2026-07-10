from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import EffectPreset, Job, Music, Project, Style
from app.schemas import DraftInfoOut, GenerateResponse, ProjectCreate, ProjectDetailOut, ProjectOut
from app.services.pipeline import run_generation

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    if db.get(Style, payload.style_id) is None:
        raise HTTPException(status_code=400, detail="所选画风不存在")
    if payload.music_id and db.get(Music, payload.music_id) is None:
        raise HTTPException(status_code=400, detail="所选音乐不存在")
    if payload.effect_preset_id and db.get(EffectPreset, payload.effect_preset_id) is None:
        raise HTTPException(status_code=400, detail="所选效果预设不存在")
    if payload.mode != "ppt_image":
        raise HTTPException(status_code=400, detail="当前仅支持 PPT 图片模式，AI短片拼接模式即将推出")

    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("/{project_id}/generate", response_model=GenerateResponse)
def generate_project(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    job = Job(project_id=project.id, status="pending")
    db.add(job)
    project.status = "generating"
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_generation, job.id)
    return GenerateResponse(job_id=job.id)


@router.get("/{project_id}/draft", response_model=DraftInfoOut)
def get_project_draft(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None or not project.video_path:
        raise HTTPException(status_code=404, detail="剪映草稿尚未生成")
    return DraftInfoOut(draft_name=project.video_path, drafts_dir=settings.jianying_drafts_dir)
