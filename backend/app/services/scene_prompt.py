import re

from app.models import Style
from app.providers.llm.minimax_llm import MiniMaxLLMProvider

llm_provider = MiniMaxLLMProvider()

SYSTEM_PROMPT = """你是一名"情感可视化脚本工程师"，负责把单句场景旁白压缩成两段可以直接喂给生图模型(img_prompt)和轻动画模型(video_prompt)的提示词。

## 输出格式（严格按下面两行输出，不要用JSON、不要用代码块、不要输出任何多余的解释文字）
IMG_PROMPT: 场景主体+表情姿态+配角描述+环境元素+色彩构图+风格锚点（写成一段连贯文字）
VIDEO_PROMPT: 5秒场景：主体<动作>，配角<互动>，镜头<轻微运动>，转场描述（写成一段连贯文字）

## img_prompt 撰写规则（固定顺序）

1. 场景主体声明（约25%篇幅）：<时间/场景>，主体<动作/姿态>
2. 表情与姿态（约15%）：表情<好奇/思考/微笑/惊讶/平静/困惑/专注>，姿态<站/坐/走/举手/点头>
3. 配角描述（约15%，没有配角就写"No supporting characters"，若整体用中文撰写则写"无配角"）：

配角视觉体系：
- 互动对象/群体：2-4个简化人形剪影，与主体同场景，可有简单表情，用于社交/群体互动场景
- 对话对象：单个简化人形，靠近主体，用于对话/倾听/沟通场景
- 心理概念拟人：单个或多个彩色轮廓（配合概念用色），用于情绪/心理概念可视化
- 思绪/念头：半透明浅色轮廓，位于主体头部上方或旁侧，带思考气泡效果，用于展示内心想法
- 陪伴/支持者：浅灰或暖灰色轮廓，位于主体旁侧或后方，用于陪伴/支持/团队场景

数量控制：一对一场景1个配角；小群体场景2-4个；群体概念4-6个，保持画面干净可读。

4. 环境元素（约15%）：背景<根据主题自动匹配的色调>，元素<简单物件形状>

主题→背景色自动匹配表：
- 认知/思考/学习 → 浅蓝/天蓝，清新平静
- 情感/感受/共情 → 浅橙/暖杏，温暖亲切
- 压力/挑战/问题 → 浅灰蓝/中性灰，略有分量感但不压抑
- 成长/改变/突破 → 浅绿/薄荷绿，生机感
- 关系/沟通/连接 → 浅紫/薰衣草紫，包容柔和
- 平静/放松/疗愈 → 米白/象牙白，大留白，纸质感
- 动机/目标/行动 → 浅黄/柠檬黄，积极明快
- 自省/内观/自我 → 浅灰紫/暗粉，内敛安静

5. 色彩与构图（约15%）：色板<主色[背景主题色]，辅助色浅灰/白，主体线条色>，构图<根据场景类型调整主体位置和留白比例>

场景→构图自动匹配表：
- 概念讲解 → 主体居中，均衡留白40-50%
- 对比展示 → 左右分布，主体与对比元素各占一侧
- 流程演示 → 主体居左，右侧留给箭头/流程元素
- 情绪展示 → 主体居中偏下，上方留白用于情绪特写
- 互动场景 → 多个角色均匀分布，保持视觉平衡
- 焦点特写 → 主体居中放大，留白30%，突出重点
- 群体场景 → 主体与配角呈三角或弧形排布

6. 风格锚点（约15%，完全固定，不要改写）：
__STYLE_ANCHOR__

## video_prompt 撰写规则

"5秒场景：主体<动作>，配角<互动动作>，镜头<轻微运动：轻微推进1-2%/轻微平移2%/静止不动/轻微拉远1.5%>，转场描述（如：平滑过渡/温暖平滑转场/明快过渡）"

请严格按 "IMG_PROMPT: ..." 和 "VIDEO_PROMPT: ..." 两行输出。img_prompt 和 video_prompt 的场景描述部分：默认使用英文撰写；只有当输入的旁白原文本身是中文时，才改用中文撰写。风格锚点部分保持原文不译。

__TEXT_POLICY__

重要：上面几条规则(1-6)里出现的中文词汇（如"色板"、"构图"、"背景"、"辅助色"等）只是给你解释规则用的，不是要你原样抄进输出里。如果你决定用英文撰写这一句img_prompt，那么从头到尾都必须是英文，包括环境元素、色彩构图这几部分也要翻译成英文描述（例如"color palette: soft blue background, light gray accents, black linework"、"composition: subject centered, 40% negative space"），不能保留任何中文字词或中文标点。写完后自查一遍，确认没有遗漏的汉字。"""

# 不同文生图模型对"画面内文字"的能力差异很大，提示词策略要分开走
TEXT_POLICY_NO_TEXT = """## 画面内文字规则（重要）

场景描述里绝对不能包含任何具体的文字、标语、屏幕上的字句或数字内容——只描述"有一块屏幕/一份文件/一个牌子"这类物件轮廓，不描述上面写了什么。当前使用的生图模型画不出可读的文字，硬要求写字只会得到一堆乱码字形。"""

TEXT_POLICY_ALLOW_TEXT = """## 画面内文字规则（重要）

当前使用的生图模型能准确渲染英文文字。为了让画面本身带一点信息量，你**可以**在 img_prompt 里要求画面出现一个极短的英文标签（1-3个单词，全大写），写在牌子、白板、卡片或标签上，用来点明这一句旁白的核心概念（例如 IMBALANCE、DAY MASTER、FIVE ELEMENTS）。

约束：
- 整张图最多出现一处文字，且必须用双引号明确写出要渲染的确切词，例如：a small sign with the text "DAY MASTER" written on it in bold capital letters
- 只能用英文单词，不能写中文，不能写句子、段落或数字编号
- 这个词必须是真实存在、拼写正确的英文单词或词组
- 如果这一句旁白比较抽象、想不出合适的短词，就不要放文字，只用箭头/圆圈/下划线这类符号标记"""


def _strip_think(content: str) -> str:
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


def _extract_prompts(content: str) -> tuple[str, str]:
    img_match = re.search(r"IMG_PROMPT:\s*(.+?)(?:\n\s*VIDEO_PROMPT:|$)", content, re.DOTALL)
    video_match = re.search(r"VIDEO_PROMPT:\s*(.+)", content, re.DOTALL)
    if not img_match:
        raise ValueError(f"未找到 IMG_PROMPT: {content[:200]}")
    img_prompt = img_match.group(1).strip()
    video_prompt = video_match.group(1).strip() if video_match else ""
    return img_prompt, video_prompt


def build_character_prompt(style: Style) -> tuple[str, str]:
    """返回 (prompt, negative_prompt)，用于生成角色定妆图/画风预览图（不涉及具体场景，只描述角色本体）。

    文字/水印这些要不要禁止完全交给画风自己的negative_prompt决定，不在这里写死。
    """
    # 这张图会作为参考图传给后续每一段分镜，所以必须是干净的角色本体，
    # 不能出现任何标注文字/箭头/说明——否则那些元素会被后续每张图继承下来
    prompt = (
        f"{style.prompt_suffix}\n\n"
        "Show only the character alone, standing upright facing forward in a neutral pose, "
        "on a plain empty background. This is a clean character portrait, not an annotated "
        "reference sheet: no labels, no callout text, no annotation arrows, no captions, "
        "no measurement lines, no words anywhere in the image."
    )
    negative_prompt = style.negative_prompt or ""
    return prompt, negative_prompt


def _text_policy(style: Style) -> str:
    """能准确渲染文字的模型才允许在画面里要求出现文字。"""
    return TEXT_POLICY_ALLOW_TEXT if style.image_provider == "gemini" else TEXT_POLICY_NO_TEXT


async def build_scene_prompt(segment_text: str, style: Style) -> tuple[str, str]:
    """返回 (img_prompt, video_prompt)。LLM调用失败或解析失败时抛出异常，调用方负责降级。"""
    system_prompt = SYSTEM_PROMPT.replace(
        "__STYLE_ANCHOR__", style.prompt_suffix or "无特殊风格锚点"
    ).replace("__TEXT_POLICY__", _text_policy(style))
    user_prompt = f"content: {segment_text}"

    raw = await llm_provider.chat(system_prompt, user_prompt)
    cleaned = _strip_think(raw)
    return _extract_prompts(cleaned)
