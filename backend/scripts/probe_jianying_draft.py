"""一次性验证脚本：确认 pyjianyingdraft 在本机剪映版本下的实际效果。

用法：
    ../.venv/Scripts/python probe_jianying_draft.py

跑完后打开剪映App -> 草稿箱，找到名为 "probe_test_xxx" 的草稿手动打开确认：
- 图片有从 1.0 到 1.06 的缓慢放大（模拟推镜）
- 字幕："这是一句测试字幕" 白字黑边，贴近底部，字号看起来正常
- 特效轨能加载 "震动" 和 "荧幕噪点" 两个特效并能预览播放

确认没问题后这个脚本可以删除，不进正式代码路径。
"""

import uuid
from pathlib import Path

import pyJianYingDraft as pyd
from pyJianYingDraft import (
    ClipSettings,
    DraftFolder,
    KeyframeProperty,
    TextBorder,
    TextStyle,
    TrackType,
    VideoSceneEffectType,
    trange,
)

# 剪映默认草稿文件夹（本机检测到的路径，如果你在剪映"全局设置->草稿位置"里改过，
# 把下面这行换成实际路径）
DRAFTS_DIR = r"C:\Users\22460\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"

# 随便找了一张之前跑ffmpeg流程时生成的分镜图来做测试
TEST_IMAGE = Path(
    r"D:\WIKIFX项目\AI火柴人\backend\storage\projects\755fb60dd1ef4fcb8c5ddee903f00513\segment_0.png"
)

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
SEG_DURATION = "5s"


def main() -> None:
    if not TEST_IMAGE.exists():
        raise FileNotFoundError(f"测试图片不存在: {TEST_IMAGE}")

    draft_name = f"probe_test_{uuid.uuid4().hex[:6]}"
    folder = DraftFolder(DRAFTS_DIR)
    script = folder.create_draft(draft_name, CANVAS_WIDTH, CANVAS_HEIGHT, fps=30)

    # --- 视频轨：1张图 + 推镜关键帧 ---
    video_track = script.append_track(pyd.TrackSpec(TrackType.video, name="body"))
    seg_range = trange("0s", SEG_DURATION)
    video_seg = pyd.VideoSegment(str(TEST_IMAGE), seg_range)
    video_seg.add_keyframe(KeyframeProperty.uniform_scale, "0s", 1.0)
    video_seg.add_keyframe(KeyframeProperty.uniform_scale, SEG_DURATION, 1.06)
    script.add_segment(video_seg, video_track)

    # --- 字幕轨 ---
    text_track = script.append_track(pyd.TrackSpec(TrackType.text, name="captions"))
    text_seg = pyd.TextSegment(
        "这是一句测试字幕",
        seg_range,
        font=pyd.FontType.高字标志圆,
        style=TextStyle(size=8.0, color=(1.0, 1.0, 1.0), align=1, auto_wrapping=True),
        border=TextBorder(color=(0.0, 0.0, 0.0), width=40.0),
        clip_settings=ClipSettings(scale_x=1.5, scale_y=1.5, transform_y=-0.83),
    )
    script.add_segment(text_seg, text_track)

    # --- 特效轨：震动 + 荧幕噪点，各占一条轨道，覆盖全片 ---
    script.append_track(pyd.TrackSpec(TrackType.effect, name="fx_shake"))
    script.append_track(pyd.TrackSpec(TrackType.effect, name="fx_noise"))
    script.add_effect(VideoSceneEffectType.震动, seg_range, track_name="fx_shake")
    script.add_effect(VideoSceneEffectType.荧幕噪点, seg_range, track_name="fx_noise")

    script.save()
    print(f"草稿已生成: {draft_name}")
    print(f"位置: {DRAFTS_DIR}\\{draft_name}")
    print("请打开剪映App -> 草稿箱，找到这个草稿手动确认效果")


if __name__ == "__main__":
    main()
