from app.db import SessionLocal
from app.models import EffectPreset, Style, Template

BUILTIN_STYLES = [
    {
        "name": "彩色简笔火柴人竖屏",
        "prompt_suffix": "极简彩色简笔画风格，火柴人角色，粗线条勾边，明快撞色背景，扁平插画风格，竖版构图，无文字",
        "negative_prompt": "写实,照片,复杂背景,文字,水印,模糊",
    },
    {
        "name": "粉笔黑板风",
        "prompt_suffix": "黑板粉笔画风格，白色/彩色粉笔线条火柴人，深色黑板背景，手绘涂鸦质感，竖版构图",
        "negative_prompt": "写实,照片,文字,水印,模糊",
    },
    {
        "name": "马克笔涂鸦风",
        "prompt_suffix": "马克笔手绘涂鸦风格，粗犷线条火柴人，纸张纹理背景，明亮多彩，竖版构图",
        "negative_prompt": "写实,照片,文字,水印,模糊",
    },
    {
        # 从原 Coze 工作流 huochairen_1-draft.yaml 的"图像生成"节点里原样搬过来的画风描述
        "name": "Coze原版彩色火柴人竖屏",
        "prompt_suffix": "Head: Rounded oval head, white filling, large white space on the face, body structure: typical of stickmen, with a torso and limbs formed by slender black lines.",
        "negative_prompt": "实心黑眼、空心眼、无白底、瞳孔过大、双层瞳孔、写实、3D、干净矢量、完美几何、渐变、照片质感、复杂背景、高饱和卡通、亮面高光眼。",
    },
]


def seed_builtin_styles() -> None:
    db = SessionLocal()
    try:
        existing_names = {s.name for s in db.query(Style).filter(Style.is_builtin.is_(True)).all()}
        for style in BUILTIN_STYLES:
            if style["name"] in existing_names:
                continue
            db.add(Style(**style, is_builtin=True))
        db.commit()
    finally:
        db.close()


BUILTIN_EFFECT_PRESETS = [
    {
        "name": "经典",
        "description": "白字黑边字幕 + 荧幕噪点，无震动、无转场，稳妥的默认选择",
        "caption_font": "高字标志圆",
        "caption_size": 11.0,
        "caption_color": "#ffffff",
        "caption_border_color": "#000000",
        "caption_position": -0.83,
        "effects": [{"name": "荧幕噪点", "intensity": None}],
        "transition_name": None,
        "zoom_end_scale": 1.06,
    },
    {
        "name": "电影感",
        "description": "暗角 + 老电影质感 + 叠化转场，弱化震动，更沉稳的叙事氛围",
        "caption_font": "兰亭圆",
        "caption_size": 10.0,
        "caption_color": "#f5f5f0",
        "caption_border_color": "#000000",
        "caption_position": -0.8,
        "effects": [
            {"name": "暗角", "intensity": None},
            {"name": "老电影", "intensity": None},
            {"name": "震动", "intensity": 8},
        ],
        "transition_name": "叠化",
        "zoom_end_scale": 1.08,
    },
    {
        "name": "简洁",
        "description": "纯字幕，不加任何特效和转场，画面最干净",
        "caption_font": "高字标志圆",
        "caption_size": 11.0,
        "caption_color": "#ffffff",
        "caption_border_color": "#000000",
        "caption_position": -0.83,
        "effects": [],
        "transition_name": None,
        "zoom_end_scale": 1.05,
    },
]


def seed_builtin_effect_presets() -> None:
    db = SessionLocal()
    try:
        existing_names = {
            p.name for p in db.query(EffectPreset).filter(EffectPreset.is_builtin.is_(True)).all()
        }
        for preset in BUILTIN_EFFECT_PRESETS:
            if preset["name"] in existing_names:
                continue
            db.add(EffectPreset(**preset, is_builtin=True))
        db.commit()
    finally:
        db.close()


BUILTIN_TEMPLATES = [
    {
        # 复刻第一次真实跑通验证用的搭配：Coze原版画风 + 英文讲述音色
        "name": "原版",
        "description": "Coze原版彩色火柴人画风 + 英文讲述音色，跟最初真实验证用的搭配一致",
        "style_name": "Coze原版彩色火柴人竖屏",
        "voice_id": "English_Trustworthy_Man",
        "effect_preset_name": "经典",
    },
]


def seed_builtin_templates() -> None:
    db = SessionLocal()
    try:
        existing_names = {t.name for t in db.query(Template).filter(Template.is_builtin.is_(True)).all()}
        for tpl in BUILTIN_TEMPLATES:
            if tpl["name"] in existing_names:
                continue
            style = db.query(Style).filter(Style.name == tpl["style_name"]).first()
            if style is None:
                continue
            effect_preset = (
                db.query(EffectPreset).filter(EffectPreset.name == tpl.get("effect_preset_name")).first()
            )
            db.add(
                Template(
                    name=tpl["name"],
                    description=tpl["description"],
                    style_id=style.id,
                    voice_id=tpl["voice_id"],
                    effect_preset_id=effect_preset.id if effect_preset else None,
                    is_builtin=True,
                )
            )
        db.commit()
    finally:
        db.close()
