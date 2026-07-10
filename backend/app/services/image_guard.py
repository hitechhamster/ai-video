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


async def generate_guarded(
    provider: ImageProvider,
    prompt: str,
    negative_prompt: str = "",
    reference_image_url: str | None = None,
    enforce_monochrome: bool = False,
) -> ImageResult:
    """按画风的约束生成图片，不合格就重试。

    目前只管"必须黑白"这一条——它是唯一能被程序可靠判定、且模型确实经常违反的约束。
    重试用尽后返回最后一次的结果（宁可出一张有色的，也不要整个生成任务失败）。
    """
    result = await provider.generate(
        prompt, negative_prompt=negative_prompt, reference_image_url=reference_image_url
    )
    if not enforce_monochrome:
        return result

    for attempt in range(MAX_RETRIES):
        saturation = average_saturation(result.image_bytes)
        if saturation <= MAX_AVG_SATURATION:
            return result
        logger.warning(
            "画面违反黑白约束 (平均饱和度 %.1f > %.1f)，重新生成 (%d/%d)",
            saturation, MAX_AVG_SATURATION, attempt + 1, MAX_RETRIES,
        )
        result = await provider.generate(
            prompt, negative_prompt=negative_prompt, reference_image_url=reference_image_url
        )

    return result
