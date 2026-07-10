from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Style
from app.providers.image import get_image_provider
from app.schemas import StyleCreate, StyleOut
from app.services.scene_prompt import build_character_prompt

router = APIRouter(prefix="/styles", tags=["styles"])


@router.get("", response_model=list[StyleOut])
def list_styles(db: Session = Depends(get_db)):
    return db.query(Style).order_by(Style.created_at).all()


@router.post("", response_model=StyleOut)
def create_style(payload: StyleCreate, db: Session = Depends(get_db)):
    style = Style(**payload.model_dump())
    db.add(style)
    db.commit()
    db.refresh(style)
    return style


@router.put("/{style_id}", response_model=StyleOut)
def update_style(style_id: str, payload: StyleCreate, db: Session = Depends(get_db)):
    style = db.get(Style, style_id)
    if style is None:
        raise HTTPException(status_code=404, detail="画风不存在")
    if style.is_builtin:
        raise HTTPException(status_code=400, detail="内置画风不可修改，请新建自定义画风")
    for key, value in payload.model_dump().items():
        setattr(style, key, value)
    db.commit()
    db.refresh(style)
    return style


@router.post("/{style_id}/preview", response_model=StyleOut)
async def generate_style_preview(style_id: str, db: Session = Depends(get_db)):
    style = db.get(Style, style_id)
    if style is None:
        raise HTTPException(status_code=404, detail="画风不存在")

    prompt, negative_prompt = build_character_prompt(style)
    image_provider = get_image_provider(style.image_provider)
    try:
        result = await image_provider.generate(prompt, negative_prompt=negative_prompt)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"预览生成失败: {exc}") from exc

    preview_dir = settings.storage_path / "style_previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{style.id}.png"
    preview_path.write_bytes(result.image_bytes)

    style.thumbnail = str(preview_path)
    db.commit()
    db.refresh(style)
    return style


@router.delete("/{style_id}")
def delete_style(style_id: str, db: Session = Depends(get_db)):
    style = db.get(Style, style_id)
    if style is None:
        raise HTTPException(status_code=404, detail="画风不存在")
    if style.is_builtin:
        raise HTTPException(status_code=400, detail="内置画风不可删除")
    db.delete(style)
    db.commit()
    return {"ok": True}
