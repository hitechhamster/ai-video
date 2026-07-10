from fastapi import APIRouter, HTTPException

from app.providers.tts.minimax import MiniMaxTTSProvider
from app.schemas import VoiceOut

router = APIRouter(prefix="/voices", tags=["voices"])
tts_provider = MiniMaxTTSProvider()


@router.get("", response_model=list[VoiceOut])
async def list_voices():
    try:
        voices = await tts_provider.list_voices()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"获取音色列表失败，请检查 MINIMAX_API_KEY 配置: {exc}") from exc
    return voices
