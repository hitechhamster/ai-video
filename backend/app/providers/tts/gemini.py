import base64
import io
import wave

import httpx

from app.config import settings
from app.providers.base import AudioResult, TTSProvider

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# 接口返回的是裸 PCM（audio/L16;codec=pcm;rate=24000），既没有文件头也不告诉你时长
_PCM_CHANNELS = 1
_PCM_SAMPLE_WIDTH = 2  # L16 = 16-bit
_DEFAULT_RATE = 24000

# 从接口报错信息里拿到的完整合法音色列表（传一个不存在的音色，它会把允许值全列出来）
VOICES = [
    "achernar", "achird", "algenib", "algieba", "alnilam", "aoede", "autonoe",
    "callirrhoe", "charon", "despina", "enceladus", "erinome", "fenrir", "gacrux",
    "iapetus", "kore", "laomedeia", "leda", "orus", "puck", "pulcherrima",
    "rasalgethi", "sadachbia", "sadaltager", "schedar", "sulafat", "umbriel",
    "vindemiatrix", "zephyr", "zubenelgenubi",
]
DEFAULT_VOICE = "charon"


def _parse_rate(mime_type: str) -> int:
    """从 'audio/L16;codec=pcm;rate=24000' 里抠出采样率。"""
    for chunk in mime_type.split(";"):
        chunk = chunk.strip()
        if chunk.startswith("rate="):
            try:
                return int(chunk[len("rate="):])
            except ValueError:
                break
    return _DEFAULT_RATE


def _pcm_to_wav(pcm: bytes, rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(_PCM_CHANNELS)
        w.setsampwidth(_PCM_SAMPLE_WIDTH)
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


class GeminiTTSProvider(TTSProvider):
    """Google Gemini 语音合成适配器。

    画风选了 gemini 生图时，配音也走 Gemini 自己闭环（OpenRouter 没有可用的 TTS）。

    两个坑（真实调用探出来的）：
    1. 返回裸 PCM，没有文件头，必须自己封成 WAV 才能给 ffmpeg / 剪映用
    2. 接口不返回时长，但 PCM 是定长编码，字节数 ÷ (采样率×位深×声道) 就是精确时长
       （跟 ffprobe 读出来的结果核对过，小数点后三位一致）
    """

    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_tts_model

    def _headers(self) -> dict:
        return {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}

    async def synthesize(self, text: str, voice_id: str) -> AudioResult:
        voice = (voice_id or DEFAULT_VOICE).lower()
        if voice not in VOICES:
            voice = DEFAULT_VOICE

        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }

        url = f"{API_BASE}/{self._model}:generateContent"
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, headers=self._headers(), json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini TTS 失败: {resp.status_code} {resp.text[:500]}")
            body = resp.json()

        candidates = body.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini TTS 无候选结果: {str(body)[:500]}")

        for part in candidates[0].get("content", {}).get("parts", []):
            inline = part.get("inlineData")
            if not (inline and inline.get("data")):
                continue
            pcm = base64.b64decode(inline["data"])
            rate = _parse_rate(inline.get("mimeType", ""))
            duration = len(pcm) / (rate * _PCM_CHANNELS * _PCM_SAMPLE_WIDTH)
            return AudioResult(
                audio_bytes=_pcm_to_wav(pcm, rate), duration_seconds=duration, format="wav"
            )

        finish_reason = candidates[0].get("finishReason")
        raise RuntimeError(f"Gemini TTS 返回结果里没有音频 (finishReason={finish_reason})")

    async def list_voices(self) -> list[dict]:
        return [{"voice_id": v, "voice_name": v.capitalize()} for v in VOICES]
