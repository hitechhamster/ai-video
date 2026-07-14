"""每日选题 + 用 LLM 写稿 + 生成 YouTube 元数据。

选题从一个轮换题库里取（用过的记在 .topic_state.json，转完一圈再从头），
再让 LLM 按"长衫先生教学系列"的调性写出旁白脚本 + YouTube 标题/描述/标签。
所有产出都是英文（面向英文观众讲中国命理文化）。
"""

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.providers.llm import get_llm_provider

STATE_FILE = Path(__file__).resolve().parent / ".topic_state.json"

# 轮换题库：十天干日主 + 五行关系 + 八字×风水结合。够一个月不重样。
# 都走"性格/文化/处世智慧"框架，不做吉凶预测（平台合规 + 更像知识号）。
TOPICS = [
    "The Jia Wood day master: the towering tree — upright, principled, but unbending",
    "The Yi Wood day master: the climbing vine — flexible, adaptive, quietly persistent",
    "The Bing Fire day master: the blazing sun — radiant, generous, impossible to ignore",
    "The Ding Fire day master: the candle flame — warm, focused, gentle but enduring",
    "The Wu Earth day master: the mountain — steady, reliable, slow to move",
    "The Ji Earth day master: the field soil — nurturing, humble, quietly supportive",
    "The Geng Metal day master: the raw ore and axe — decisive, tough, needs refining",
    "The Xin Metal day master: the polished jewel — refined, sensitive, values beauty",
    "The Ren Water day master: the great river — bold, resourceful, always moving",
    "The Gui Water day master: the morning dew — gentle, adaptable, easy to overlook",
    "The five elements generating cycle: how Wood feeds Fire feeds Earth",
    "The five elements controlling cycle: how Metal cuts Wood, Water quenches Fire",
    "What a balanced BaZi chart really means — and why perfect balance is rare",
    "The favorable element (Yong Shen): the one element your chart is quietly asking for",
    "Why a weak day master and a strong day master need opposite things",
    "How BaZi and Feng Shui work together: the seed and the soil",
    "If your chart is starved of Fire: warmth, light, and a bright home",
    "If your chart is drowning in Water: grounding, dryness, and solid support",
    "If your chart lacks Wood: growth, greenery, and room to expand",
    "If your chart is heavy with Earth: movement, metal, and openness",
    "Clash and combination: why some element pairings attract and others collide",
    "The Ten Gods, simply: how BaZi describes your relationships and drives",
    "Why two people with the same chart can live completely different lives",
    "Your birth hour matters: the hidden pillar most beginners ignore",
]

_SYSTEM_PROMPT = """You write scripts for a faceless YouTube Shorts channel that explains Chinese metaphysics (BaZi and Feng Shui) as culture and personality wisdom, in English, for a global audience.

Hard rules:
- This is EDUCATION and CULTURE, never fortune-telling. Never promise luck, wealth, predictions, or outcomes. Frame everything as personality, philosophy, and practical wisdom.
- The narration is 8 to 10 short sentences. ONE idea per sentence. Every sentence must end with a period so it can be split cleanly.
- The FIRST sentence is a scroll-stopping hook (a question or a surprising claim).
- Plain, vivid, spoken English. No jargon without a plain-English gloss. No emojis in the narration.
- The last sentence lands a calm takeaway (no "subscribe", no call to action inside the narration).

Output EXACTLY these four labeled blocks, nothing else, no code fences:
SCRIPT:
<the 8-10 sentence narration as one paragraph>
TITLE:
<a curiosity-driven YouTube title, <= 70 characters, no fortune-telling promises>
DESCRIPTION:
<2-3 sentence description, then a newline, then: "Follow for one idea from Chinese metaphysics per short.">
HASHTAGS:
<exactly 3 hashtags separated by spaces, most important first, e.g. #bazi #fengshui #chinesemetaphysics>"""


@dataclass
class DailyContent:
    topic: str
    script: str
    title: str
    description: str
    hashtags: list[str]


def _pick_topic() -> tuple[int, str]:
    used: list[int] = []
    if STATE_FILE.exists():
        try:
            used = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("used", [])
        except Exception:  # noqa: BLE001
            used = []
    # 全部用过就清零，重新轮
    if len(used) >= len(TOPICS):
        used = []
    for i in range(len(TOPICS)):
        if i not in used:
            return i, TOPICS[i]
    return 0, TOPICS[0]


def _mark_used(index: int) -> None:
    used: list[int] = []
    if STATE_FILE.exists():
        try:
            used = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("used", [])
        except Exception:  # noqa: BLE001
            used = []
    if len(used) >= len(TOPICS):
        used = []
    if index not in used:
        used.append(index)
    STATE_FILE.write_text(json.dumps({"used": used}, ensure_ascii=False, indent=2), encoding="utf-8")


def _block(label: str, text: str) -> str:
    m = re.search(rf"{label}:\s*(.+?)(?=\n[A-Z]+:|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def generate(topic: str | None = None) -> tuple[int, DailyContent]:
    """返回 (topic_index, DailyContent)。topic 传 None 时从题库自动轮换取下一个。"""
    if topic is None:
        index, topic = _pick_topic()
    else:
        index = -1  # 外部指定的临时选题，不计入轮换状态

    llm = get_llm_provider("gemini")
    raw = asyncio.run(llm.chat(_SYSTEM_PROMPT, f"Topic: {topic}"))
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    script = _block("SCRIPT", raw)
    title = _block("TITLE", raw).strip().strip('"')
    description = _block("DESCRIPTION", raw)
    hashtags_line = _block("HASHTAGS", raw)
    hashtags = [h for h in hashtags_line.split() if h.startswith("#")][:3]

    if not script or not title:
        raise RuntimeError(f"LLM 输出解析失败，原文前 300 字：\n{raw[:300]}")

    return index, DailyContent(
        topic=topic, script=script, title=title, description=description, hashtags=hashtags
    )


def commit_topic(index: int) -> None:
    """出片成功后再把选题标记为已用，避免失败也消耗题库。"""
    if index >= 0:
        _mark_used(index)
