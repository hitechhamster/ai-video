"""生成后的画面质检：Gemini 没有 negative prompt 参数，"必须黑白"这类约束只能靠正向文本，
服从度不稳定——同一句提示词，有时出彩色有时不出。实测一批9张里有3张背景整片变蓝。

对策不是继续抠提示词措辞（做过 A/B，同一提示词单独跑3次全对，证明不是措辞问题，
就是模型随机性），而是生成后量一下，超标就重生成。
"""

import io
import logging

from PIL import Image

from app.providers.base import ImageProvider, ImageResult

logger = logging.getLogger(__name__)

# 平均饱和度（HSV 的 S 通道，0-255）。
# 实测标定：干净的黑白线稿落在 1.9-5.9，背景整片染色的落在 47-115，
# 而背景只是淡淡一层灰蓝的边界样本是 14.3——取 12 能把两类干净分开。
MAX_AVG_SATURATION = 12.0

# 彩色画风的下限：允许颜色但不强制时，Gemini 会随机把几张退成灰/棕墨色。
# 实测同一批里满色的落在 40-76，退色的落在 0.8-10.5——取 15 能把"明显掉色"的挑出来，
# 又给"柔和水彩"这种低饱和但确实有色的画面留了余地。
MIN_AVG_SATURATION = 15.0

# 重试次数。实测单张漏色概率约 1/3，重试2次后仍全部漏色的概率不到 4%。
MAX_RETRIES = 2


def average_saturation(image_bytes: bytes) -> float:
    """图片的平均饱和度，纯黑白线稿接近 0。"""
    with Image.open(io.BytesIO(image_bytes)) as im:
        # 缩到 160px 够用了，全尺寸算没必要
        hsv = im.convert("RGB").resize((160, 160)).convert("HSV")
        saturations = [s for _, s, _ in hsv.getdata()]
    return sum(saturations) / len(saturations)


def is_monochrome(image_bytes: bytes) -> bool:
    return average_saturation(image_bytes) <= MAX_AVG_SATURATION


def _violates(saturation: float, enforce_monochrome: bool, enforce_color: bool) -> str | None:
    """返回违规原因（给日志用），合格返回 None。"""
    if enforce_monochrome and saturation > MAX_AVG_SATURATION:
        return f"违反黑白约束 (平均饱和度 {saturation:.1f} > {MAX_AVG_SATURATION})"
    if enforce_color and saturation < MIN_AVG_SATURATION:
        return f"上色不足、接近灰阶 (平均饱和度 {saturation:.1f} < {MIN_AVG_SATURATION})"
    return None


async def generate_guarded(
    provider: ImageProvider,
    prompt: str,
    negative_prompt: str = "",
    reference_image_url: str | None = None,
    enforce_monochrome: bool = False,
    enforce_color: bool = False,
) -> ImageResult:
    """按画风的约束生成图片，不合格就重试。

    两条互斥的约束都靠同一个平均饱和度指标判定：
    - enforce_monochrome：必须黑白，饱和度超上限就重生成；
    - enforce_color：必须有色，饱和度低于下限（画面掉成灰阶）就重生成。
    重试用尽后返回最后一次的结果（宁可出一张不达标的，也不要整个生成任务失败）。
    """
    result = await provider.generate(
        prompt, negative_prompt=negative_prompt, reference_image_url=reference_image_url
    )
    if not (enforce_monochrome or enforce_color):
        return result

    for attempt in range(MAX_RETRIES):
        reason = _violates(average_saturation(result.image_bytes), enforce_monochrome, enforce_color)
        if reason is None:
            return result
        logger.warning("画面%s，重新生成 (%d/%d)", reason, attempt + 1, MAX_RETRIES)
        result = await provider.generate(
            prompt, negative_prompt=negative_prompt, reference_image_url=reference_image_url
        )

    return result
